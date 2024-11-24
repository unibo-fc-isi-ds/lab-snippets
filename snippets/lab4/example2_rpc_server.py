from snippets.lab3 import Server
from snippets.lab4.users import Role, Token
from snippets.lab4.users.impl import InMemoryUserDatabase,InMemoryAuthenticationService
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
                try:
                    print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Received payload: {payload}')
                    request = deserialize(payload)
                    assert isinstance(request, Request)
                    print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Unmarshalled request: {request}')
                    response = self.__handle_request(request)
                    serialized_response = serialize(response)
                    print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Sending response: {response}')
                    connection.send(serialized_response)
                except Exception as e:
                    print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Error processing message: {e}')
                    traceback.print_exc()
                    error_response = Response(None, str(e))
                    connection.send(serialize(error_response))
                finally:
                    connection.close()
                    print('[%s:%d] Close connection' % connection.remote_address)
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)

    def __check_authorization(self, request: Request, required_role: Role = Role.ADMIN):
        if 'token' not in request.metadata:
            raise ValueError("Authentication required")
        
        token = request.metadata['token']
        # 确保 token 是 Token 类型
        if not isinstance(token, Token):
            raise ValueError("Invalid token format")
            
        if not self.__auth_service.validate_token(token):
            raise ValueError("Invalid or expired token")
            
        if token.user.role != required_role:
            raise ValueError(f"Operation requires {required_role.name} role")

    def __handle_request(self, request):
        try:
            # Check authorization for sensitive operations
            sensitive_operations = {'get_user'}
            if request.name in sensitive_operations:
                self.__check_authorization(request)

            if hasattr(self.__user_db, request.name):
                method = getattr(self.__user_db, request.name)
            elif hasattr(self.__auth_service, request.name):
                method = getattr(self.__auth_service, request.name)
            else:
                raise ValueError(f"Method {request.name} not found")

            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = " ".join(str(arg) for arg in e.args)
            traceback.print_exc()
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