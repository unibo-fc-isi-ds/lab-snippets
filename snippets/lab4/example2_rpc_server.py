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
    
    def __handle_request(self, request):
        try:
            if hasattr(self.__auth_service, request.name):
                service = self.__auth_service
            elif hasattr(self.__user_db, request.name):
                service = self.__user_db
            else:
                raise AttributeError(f"Method '{request.name}' not found on any service.")
            method = getattr(service, request.name) 
            if service is self.__user_db and request.name == 'get_user':
                token_data = request.metadata.get('token') if request.metadata else None
                if not token_data:
                    raise PermissionError("Authentication required: Missing token in metadata.")
                token_obj = token_data 
                if not self.__auth_service.validate_token(token_obj):
                    raise PermissionError("Authentication failed: Invalid or expired token.")
                if token_obj.user.role != Role.ADMIN:
                    raise PermissionError("Authorization failed: User must have 'admin' role to read user data.")

            result = method(*request.args)
            error = None
            
        except PermissionError as e: 
            result = None
            error = "Authorization/Authentication Error: " + " ".join(e.args) 
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
