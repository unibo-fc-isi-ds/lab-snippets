from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.users import Role, Token
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    PROTECTED_METHODS = {'get_user'}

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
                print('[%s:%d] Unmarshall request:' % connection.remote_address, request.name)
                response = self.__handle_request(request)
                connection.send(serialize(response))
                print('[%s:%d] Marshall response' % connection.remote_address)
                connection.close()
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)

    def __check_authorization(self, request: Request) -> tuple[bool, str | None]:
        """
        Check if the request is authorized.
        Returns (is_authorized, error_message).
        """
        if request.name not in self.PROTECTED_METHODS:
            return True, None

        if not request.metadata or 'token' not in request.metadata:
            return False, "Authentication required: missing token"

        token_data = request.metadata['token']

        # Reconstruct token object
        try:
            token = Token(
                user=token_data['user'],
                expiration=token_data['expiration'],
                signature=token_data['signature']
            )
        except (KeyError, TypeError) as e:
            return False, f"Invalid token format: {e}"

        if not self.__auth_service.validate_token(token):
            return False, "Invalid or expired token"

        if token.user.role != Role.ADMIN:
            return False, "Authorization failed: admin role required"

        return True, None

    def __handle_request(self, request):
        """
        Route requests to the appropriate service based on method name.
        Check authorization for protected methods.
        """
        try:
            is_authorized, error_msg = self.__check_authorization(request)
            if not is_authorized:
                return Response(None, error_msg)

            if hasattr(self.__user_db, request.name):
                service = self.__user_db
            elif hasattr(self.__auth_service, request.name):
                service = self.__auth_service
            else:
                raise AttributeError(f"Method '{request.name}' not found in any service")

            method = getattr(service, request.name)
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