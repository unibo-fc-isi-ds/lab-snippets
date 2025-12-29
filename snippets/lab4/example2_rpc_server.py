from snippets.lab3 import Server
from snippets.lab4.users import Role, Token
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth_service = InMemoryAuthenticationService(self.__user_db)

    def __check_token(self, request: Request):
        token = request.metadata
        if token is None:
            raise PermissionError("Request missing token")
        if not self.__auth_service.validate_token(token):
            raise PermissionError("Invalid or expired token")
    
    def __on_connection_event(self, event, connection, address, error):
        match event:
            case 'listen':
                print('Server listening on %s:%d' % address)
            case 'connect':
                connection.callback = self.__on_message_event
            case 'error':
                # traceback.print_exception(error)
                print(error, file=sys.stderr)
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
                # traceback.print_exception(error)
                print(error, file=sys.stderr)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)
    
    def __handle_request(self, request: Request):
        try:
            # If method not found yet, try auth service
            method = None
            if hasattr(self.__user_db, request.name) and not hasattr(self.__auth_service, request.name):
                if request.name == "get_user":
                    self.__check_token(request)
                    if request.metadata.user.role != Role.ADMIN:
                        raise PermissionError("Only admin can perform this operation")
                method = getattr(self.__user_db, request.name)
            elif hasattr(self.__auth_service, request.name) and not hasattr(self.__user_db, request.name):
                    method = getattr(self.__auth_service, request.name)
            if method is None: # If still not found, raise error
                raise AttributeError(f"Invalid operation")
            # Execute method
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
