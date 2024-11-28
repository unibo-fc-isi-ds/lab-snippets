from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


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
        #try:
            #raise Exception(request.name)
            if(request.name=='authenticate'):
                result=self.__auth_db.authenticate(*request.args)
                #e se autenticazione non valida?
                error=None
            else:
                if(request.name!='add_user'):
                    #the token is needed
                    if(request.metadata!=None and self.__auth_db.validate_token(request.metadata)):
                        #the token is valid
                        method = getattr(self.__user_db, request.name) # get the method from the user database
                        result = method(*request.args) # call the method with the arguments, store the result
                        error = None # no error occurred in this case
                    else:
                        #the token is not valid
                        result=None
                        error="Invalid authentication token"
                else:
                #the token is not needed for this operation
                    method = getattr(self.__user_db, request.name) # get the method from the user database
                    result = method(*request.args) # call the method with the arguments, store the result
                    error = None # no error occurred in this case

        #except Exception as e: # if an error occurs:
        #    result = None # no result in case of an error
        #    error = " ".join(e.args) # store the error message
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
