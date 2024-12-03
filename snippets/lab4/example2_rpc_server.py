from snippets.lab3 import Server
from snippets.lab4.example0_users import _PRINT_LOGS
from snippets.lab4.users.impl import InMemoryAuthenticationService, InMemoryUserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    def __init__(self, port):
        """
        Initialize the server with user database and authentication service.
        """
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase(debug=_PRINT_LOGS)
        self.__auth_service = InMemoryAuthenticationService(self.__user_db, debug=_PRINT_LOGS)

    def __on_connection_event(self, event, connection, address, error):
        """
        Handle server-level events such as listening, connecting, and errors.
        """
        match event:
            case 'listen':
                print(f'Server listening on {address[0]}:{address[1]}')
            case 'connect':
                connection.callback = self.__on_message_event
            case 'error':
                traceback.print_exception(error)
            case 'stop':
                print('Server stopped')

    def __on_message_event(self, event, payload, connection, error):
        """
        Handle connection-level events such as receiving messages or closing connections.
        """
        match event:
            case 'message':
                print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Open connection')
                try:
                    request = deserialize(payload)
                    assert isinstance(request, Request)
                    print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Unmarshall request:', request)
                    
                    response = self.__handle_request(request)
                    connection.send(serialize(response))
                    
                    print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Marshall response:', response)
                except Exception as e:
                    traceback.print_exception(e)
                    response = Response(None, "Server encountered an error")
                    connection.send(serialize(response))
                finally:
                    connection.close()
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Close connection')

    def __handle_request(self, request):
        """
        Process a client request by invoking the appropriate service or database method.
        """
        try:
            # Authorization checks for "get_user"
            if request.name == 'get_user':
                token = request.metadata
                if not token or not self.__auth_service.validate_token(token):
                    return Response(None, "Access denied: Missing or invalid token.")
                if token.user.role.name.upper() != "ADMIN":
                    return Response(None, "Access denied: Admin privileges required.")

            # Determine whether to use auth_service or user_db
            if hasattr(self.__auth_service, request.name):
                method = getattr(self.__auth_service, request.name)
            elif hasattr(self.__user_db, request.name):
                method = getattr(self.__user_db, request.name)
            else:
                return Response(None, f"Unknown method: {request.name}")

            # Execute the method and return the result
            result = method(*request.args)
            return Response(result, None)
        except Exception as e:
            return Response(None, " ".join(e.args))


if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
