from snippets.lab3 import Server
from snippets.lab4.users import Role
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

    def __check_authorization(self, request: Request, required_role: Role = None):
        """
        Check if the request has a token and the user is authorized. If not throw an Error
        """
        # check the token presence
        if not request.metadata or 'token' not in request.metadata:
            raise PermissionError("Authentication required")

        token = request.metadata['token']

        # Check token validity
        if not self.__auth_service.validate_token(token):
            raise PermissionError("Invalid or expired token")

        # Check if the role is that one required.
        if required_role and token.user.role != required_role:
            raise PermissionError(f"Role {required_role.name} required")
    
    def __handle_request(self, request):
        try:
            # Admin operations
            if request.name == 'get_user':
                self.__check_authorization(request, required_role=Role.ADMIN)

            if hasattr(self.__user_db, request.name):
                method = getattr(self.__user_db, request.name)
            elif hasattr(self.__auth_service, request.name):
                method = getattr(self.__auth_service, request.name)
            else:
                raise AttributeError(f'Unknown method: {request.name}')
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
