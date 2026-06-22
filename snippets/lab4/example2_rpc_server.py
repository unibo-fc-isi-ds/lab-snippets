from snippets.lab3 import Server
from snippets.lab4.users import Role
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService, AuthenticationService, \
    UserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    def __init__(self, port: int):
        super().__init__(port, self.__on_connection_event)
        self.__user_db: UserDatabase = InMemoryUserDatabase()
        self.__auth_service: AuthenticationService = InMemoryAuthenticationService(self.__user_db)
        self.__protected_methods: set[str] = {'get_user'}

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
            if request.name in self.__protected_methods:
                self.__verify_access(request.metadata)

            if hasattr(self.__user_db, request.name):
                method = getattr(self.__user_db, request.name)
            elif hasattr(self.__auth_service, request.name):
                method = getattr(self.__auth_service, request.name)
            else:
                raise AttributeError(f"Unknown method: {request.name}")

            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = " ".join(e.args)
        return Response(result, error)

    def __verify_access(self, token):
        """Check token presence, validity, and admin role."""
        if token is None:
            raise PermissionError("Authentication required")

        if not self.__auth_service.validate_token(token):
            raise PermissionError("Invalid or expired token")

        user = self.__user_db.get_user(token.user.username)
        if user.role != Role.ADMIN:
            raise PermissionError("Admin privileges required")


if __name__ == '__main__':
    import sys

    server = ServerStub(int(sys.argv[1]))
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
