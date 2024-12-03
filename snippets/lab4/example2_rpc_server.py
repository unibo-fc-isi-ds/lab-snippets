from datetime import timedelta
from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback
from snippets.lab4.users import Role

TIME=timedelta(hours=2)

class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth_db = InMemoryAuthenticationService(database=self.__user_db, secret=None, debug=True)
    
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
    
    def __on_message_event(self, event, payload, connection, error):
        match event:
            case 'message':
                print('[%s:%d] Open connection' % connection.remote_address)
                request = deserialize(payload)
                assert isinstance(request, Request)
                print('[%s:%d] Unmarshall request:' % connection.remote_address, request)
                response = self.__handle_request(request)
                connection.send(serialize(response))
                print('[%s:%d] Marshall response:' % connection.remote_address, response)
                connection.close()
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)
    
    def __handle_request(self, request:Request): # this is where the actual function to execute is selecte and executed
        try:
            match request.name:
                case 'authenticate':
                    #no token is needed, as it's generated by this operation
                    result=self.__auth_db.authenticate(*request.args, duration=TIME)
                    #If authentication is not valid, an exeption is raised
                    error=None
                case 'add_user':
                    #the token is not needed for add users
                    method = getattr(self.__user_db, request.name) # get the method from the user database
                    result = method(*request.args) # call the method with the arguments, store the result
                    #If adding the user failed, an exeption is raised
                    error = None 
                case 'get_user':
                    if(request.metadata!=None):
                        #the token is needed for get_users
                        if(self.__auth_db.validate_token(request.metadata)):
                            #the token is valid
                            if(request.metadata.user.role==Role.ADMIN):
                                #the token is valid and it's of an admin
                                method = getattr(self.__user_db, request.name) # get the method from the user database
                                result = method(*request.args) # call the method with the arguments, store the result
                                error = None # no error occurred in this case
                            else:
                                result=None
                                error="This action can only be done by admin users"
                        else:
                            result=None
                            error="Token not valid, please authenticate"
                    else:
                        #the token is not valid
                        result=None
                        error="Missing token, please authenticate"
                case 'check_password':
                    if(request.metadata!=None):
                        #the token is needed for check_password
                        if(self.__auth_db.validate_token(request.metadata)):
                        #the token is valid
                            method = getattr(self.__user_db, request.name) # get the method from the user database
                            result = method(*request.args) # call the method with the arguments, store the result
                            error = None # no error occurred in this case
                        else:
                            result=None
                            error="Token not valid, please authenticate"
                    else:
                        #the token is not valid
                        result=None
                        error="Missing token, please authenticate"
                case _:
                    print(request.name)
                    result=None
                    error="Unknown command"

        except Exception as e: # if an error occurs:
            result = None # no result in case of an error
            error = " ".join(e.args) # store the error message
        return Response(result, error) # return a Response object with the result and the error message


if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
