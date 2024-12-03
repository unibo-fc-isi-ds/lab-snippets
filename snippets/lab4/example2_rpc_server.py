from snippets.lab3 import Server
from snippets.lab4.example0_users import _PRINT_LOGS
from snippets.lab4.users.impl import InMemoryAuthenticationService, InMemoryUserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self._on_connection_event)
        self._user_db = InMemoryUserDatabase(debug=_PRINT_LOGS)
        self._auth_service = InMemoryAuthenticationService(self._user_db, debug=_PRINT_LOGS)

    def _on_connection_event(self, event, connection, address, error):
        if event == 'listen':
            print(f"Server listening on {address[0]}:{address[1]}")
        elif event == 'connect':
            connection.callback = self._on_message_event
        elif event == 'error':
            traceback.print_exception(error)
        elif event == 'stop':
            print("Server stopped")

    def _on_message_event(self, event, payload, connection, error):
        if event == 'message':
            self._handle_message(payload, connection)
        elif event == 'error':
            traceback.print_exception(error)
        elif event == 'close':
            print(f"[{connection.remote_address[0]}:{connection.remote_address[1]}] Connection closed")

    def _handle_message(self, payload, connection):
        try:
            print(f"[{connection.remote_address[0]}:{connection.remote_address[1]}] Open connection")
            request = deserialize(payload)
            if not isinstance(request, Request):
                raise ValueError("Invalid request format")
            print(f"[{connection.remote_address[0]}:{connection.remote_address[1]}] Unmarshalled request:", request)
            response = self._handle_request(request)
        except Exception as e:
            response = Response(None, f"Request handling error: {e}")
        connection.send(serialize(response))
        print(f"[{connection.remote_address[0]}:{connection.remote_address[1]}] Marshalled response:", response)
        connection.close()

    def _handle_request(self, request):
        try:
            # Ensure the user is authenticated and has appropriate permissions
            if request.name == 'get_user':
                token = request.metadata
                if not token or not self._auth_service.validate_token(token):
                    return Response(None, "Access denied: Missing or invalid token.")
                if token.user.role.name.upper() != "ADMIN":
                    return Response(None, "Access denied: Admin privileges required.")

            # Dynamically resolve the appropriate method
            if hasattr(self._auth_service, request.name):
                method = getattr(self._auth_service, request.name)
            elif hasattr(self._user_db, request.name):
                method = getattr(self._user_db, request.name)
            else:
                raise ValueError(f"Unknown method: {request.name}")

            result = method(*request.args)
            return Response(result, None)
        except Exception as e:
            return Response(None, f"Error executing {request.name}: {e}")

if __name__ == '__main__':
    import sys
    try:
        port = int(sys.argv[1])
        server = ServerStub(port)
        print(f"Server running on port {port}.")
        while True:
            input('Press Ctrl+D (Unix) or Ctrl+Z (Win) to stop the server.\n')
    except (EOFError, KeyboardInterrupt):
        print("\nShutting down server.")
    finally:
        server.close()
