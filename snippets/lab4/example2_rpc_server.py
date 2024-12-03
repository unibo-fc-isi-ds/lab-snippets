from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback
from .users.impl import *

class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase(debug=True)
        self.__auth_service = InMemoryAuthenticationService(self.__user_db, debug=True)
    
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
            method = None
            match request.name:
                case 'add_user'| 'check_password':
                    method = getattr(self.__user_db, request.name)
                case 'get_user':
                    if request.token is None:
                        raise ValueError("Token is required to perform this operation")
                    if not self.__auth_service.validate_token(request.token):
                        raise ValueError("Invalid token")
                    if request.token.user.role != Role.ADMIN:
                        raise ValueError("Unauthorized")
                    method = getattr(self.__user_db, request.name)
                case 'authenticate'| 'validate_token':
                    method = getattr(self.__auth_service, request.name)
            print(f"Calling {request.name} with args: {request.args[0]}")
            result = method(request.args[0])
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
            user_input = input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
