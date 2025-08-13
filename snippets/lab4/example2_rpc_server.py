from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback
from snippets.lab4.users import Role


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth_service = InMemoryAuthenticationService(self.__user_db)
    
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
                
                # print("payload: ", payload)
                request = deserialize(payload)
                assert isinstance(request, Request)
                print('[%s:%d] Unmarshall request:' % connection.remote_address, request)
                # print(f"Request name: {request.name}")
            
                if request.name == 'get_user':
                    # print(f"\nChecking authorization with token: {request.metadata}")
                    if not self.__authorization(request.metadata):
                        print("Checking authorization failed\n")
                        response = Response(None, 'Unauthorized')
                        connection.send(serialize(response))
                        connection.close()
                        return
                    else:
                        print("Checking authorization successed\n")
                
                response = self.__handle_request(request)
                connection.send(serialize(response))
                print('[%s:%d] Marshall response:' % connection.remote_address, response)
                connection.close()
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)
    
    def __handle_request(self, request):
        try:
            method = getattr(self.__user_db, request.name)
            result = method(*request.args)
            error = None 
            return Response(result, error)
        except Exception as e:
            pass
        
        try:
            method = getattr(self.__auth_service, request.name)
            result = method(*request.args)
            error = None 
            return Response(result, error)
        except Exception as e:
            result = None
            error = " ".join(e.args)
        
        return Response(result, error)
    
    def __authorization(self, token):
        if token is None:
            return False
        elif not self.__auth_service.validate_token(token):
            return False
        elif not token.user.role == Role.ADMIN:
            return False
        return True

if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
