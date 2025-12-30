from snippets.lab3 import Server
from snippets.lab4.users import Token, UserDatabase, AuthenticationService
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


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
            method = getattr(self.__user_db, request.name, None) or \
                    getattr(self.__auth_service, request.name, None)
            if_method = getattr(UserDatabase, request.name, None) or \
                    getattr(AuthenticationService, request.name, None)
            if method is None:
                raise ValueError('Procedure %s not found' % request.name)
            if hasattr(if_method, 'requires_auth') and if_method.requires_auth:
                if not isinstance(request.metadata, Token):
                    raise ValueError('Authentication is required')
                token = request.metadata
                if not self.__auth_service.validate_token(token):
                    raise ValueError('Invalid token')
                if hasattr(if_method, 'allowed_roles') and token.user.role not in if_method.allowed_roles:
                    raise ValueError('Missing permission')
            result = method(*request.args)
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
