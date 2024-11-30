import sys
import os

from snippets.lab4.users import Role
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))


from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryAuthenticationService, InMemoryUserDatabase
from snippets.lab4.example1_presentation import DEFAULT_DESERIALIZER, serialize, deserialize, Request, Response
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
                print(f'Received payload: {payload}')
                try:
                    request = deserialize(payload)
                    response = self.__handle_request(request)
                    connection.send(serialize(response))
                    print(f'Sent response: {response}')
                except Exception as e:
                    print(f'Error processing request: {e}')
                    connection.send(serialize(Response(None, str(e))))
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)
    
    def __handle_request(self, request):
        try:
            print(f"Handling request: {request.name}")
            print(f"Arguments before method call: {request.args}")
            print(f"Metadata: {request.metadata}")

        # Check if the operation requires authentication
            if request.name in ['get_user']:  # Add other admin-only methods here
                if not request.metadata or 'token' not in request.metadata:
                    raise ValueError("Authentication required")
            
                token = self.__auth_service.deserialize_token(request.metadata['token'])
                if not self.__auth_service.validate_token(token):
                    raise ValueError("Invalid or expired token")

            # Ensure the user has the admin role
                if token.user.role != Role.ADMIN:
                    raise PermissionError("Unauthorized access: Admin role required")

        # Determine the appropriate service
            service = self.__user_db if hasattr(self.__user_db, request.name) else self.__auth_service
            method = getattr(service, request.name)

        # Call the method and get the result
            result = method(*request.args)
            print(f"Result of {request.name}: {result}")
            return Response(result, None)
        except Exception as e:
            error = f"Exception occurred: {e}"
            print(error)
            return Response(None, error)



if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
