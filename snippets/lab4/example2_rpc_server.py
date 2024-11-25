from snippets.lab3 import Server
from snippets.lab4.users import Role, Token
from snippets.lab4.users.impl import InMemoryAuthenticationService, InMemoryUserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback

class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth = InMemoryAuthenticationService(self.__user_db)
    
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

    def __requires_admin(self, request_name: str) -> bool:
        return request_name in ["get_user"]

    def __can_perform_request(self, request) -> tuple[bool, str]:
        if self.__requires_admin(request.name):
            token: Token = request.metadata['token']
            if not token:
                return (False, "A token is required.")
            if not self.__auth.validate_token(token):
                return (False, "Invalid token.")
            if token.user.role != Role.ADMIN:
                return (False, f"User {token.user.username} does not have admin privileges.")
        return (True, "")

    def __handle_request(self, request):
        can_perform, err = self.__can_perform_request(request)
        if not can_perform:
            return Response(None, err)
        for backend in [self.__user_db, self.__auth]:
            method = getattr(backend, request.name, None)
            if callable(method):
                return Response(method(*request.args), None)
        return Response(None, f"Unhandled request '{request.name}'.")

if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
