from datetime import datetime
from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase
from snippets.lab4.users.impl import InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback
from .users import Role, Token


class ServerStub(Server): #an extension of the sever class
    def __init__(self, port): #we need to provide the port the server is listening upon and to provide the callback for when new conncetions arrive
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()#we initialise a new instance of the database
        # we may call self.__user_db.add_user(u), self.__user_db.get_user(u) -> user, self.__user_db.check_password 
        self.__authentication_service = InMemoryAuthenticationService(self.__user_db)

        #in order to support a secure RPC-based Authentication Service, we need to introduce a list that is going to contain all the tokens of the users that requested the authentication procedure. So whenever a user trues to get the data of another user registered,
        #if the token of the foremost does not result in the list, the operation will result in an error
        self.users_tokens: list[Token] = []
    
    def __on_connection_event(self, event, connection, address, error):
        match event:
            case 'listen':
                print('Server listening on %s:%d' % address)
            case 'connect':
                connection.callback = self.__on_message_event
            case 'error':
                traceback.print_exception(error)
            case 'stop':
                print('Server stopped')
    
    def __on_message_event(self, event, payload, connection, error): #where we handle the connections with the clients. Each connection will just send 1 message to the server stub
        match event:
            case 'message':
                print('[%s:%d] Open connection' % connection.remote_address)
                request = deserialize(payload) #payload contains the json document
                assert isinstance(request, Request)#nobody is forcing the client to behave correctly: ensuring that we actually receive the request
                print('[%s:%d] Unmarshall request:' % connection.remote_address, request)
                response = self.__handle_request(request)
                connection.send(serialize(response))
                print('[%s:%d] Marshall response:' % connection.remote_address, response)
                connection.close()
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)
    
    def __handle_request(self, request):
        #we have 3 possibilities: request.name = get_user | add_user | check_password
        user_db_valid_methods = [ 'get_user', 'add_user' , 'check_password']
        authentication_service_valid_methods = [ 'validate_token' , 'authenticate', 'get_token']

        try:
            if request.name in user_db_valid_methods:
                #if the user trying to read the information in the database does not match with any tokens or its kone is not valid, the operation will reutrn an error,
                #otherwise if no error is raised it means that the user is authorized to read the data in the database.
                if request.name == 'get_user':
                    id, reader = request.args
                    permission = False
                    for token in self.users_tokens:
                        if reader == token.user.username:
                            if (token.user.role == Role.ADMIN) and (token.expiration > datetime.now()):
                                permission = True
                                break
                    if id == reader:
                        permission = True
                    if permission == False: 
                        raise PermissionError(f"Access denied: User '{reader}' does not have authorization to read '{id}'.")
                method = getattr(self.__user_db, request.name) #self.__user_db.add_user. If I call a function that does not exit getattr would return None=>method(None) would rise the error
            elif request.name in authentication_service_valid_methods:
                #whenever a user wants to get its token, if the token was not previously created the operation will return an error; otherwise it will return the token of the user performing the request. 
                if request.name == 'get_token':
                    user = request.args[0]
                    for token in self.users_tokens:
                        if user == token.user.username:
                            return Response(result = token, error = None)
                    error = "User not authenticated"
                    result = None
                    return Response(result, error)
                method = getattr(self.__authentication_service, request.name)
            result = method(*request.args)
            #whenever a user requestst the authentication procedure, the token that is generated is put in the list of the created tokens.
            if request.name == 'authenticate':
                self.users_tokens.append(result)
            error = None
        except Exception as e:
            result = None
            error = " ".join(e.args)
        return Response(result, error)


if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
