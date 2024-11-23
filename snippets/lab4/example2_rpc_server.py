from snippets.lab3 import Server
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

    def __handle_request(self, request):
        try:
            print(f"Handling request: {request.name} with args: {request.args}")  # 添加日志

            # 确保请求的方法名称在用户数据库或认证服务中
            if hasattr(self.__user_db, request.name):
                method = getattr(self.__user_db, request.name)
            elif hasattr(self.__auth_service, request.name):
                method = getattr(self.__auth_service, request.name)
            else:
                raise ValueError(f"Method {request.name} not found")

            # 调用该方法并记录结果
            result = method(*request.args)
            print(f"Request handled successfully, result: {result}")
            error = None
        except Exception as e:
            result = None
            error = " ".join(e.args)
            print(f"Error handling request: {error}")
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
