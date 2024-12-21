from snippets.lab3 import Server
from snippets.lab4.users import Role, Token
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
                try:
                    request = deserialize(payload)
                    assert isinstance(request, Request)
                    print('[%s:%d] Unmarshall request:' % connection.remote_address, request)
                    response = self.__handle_request(request)
                # connection.send(serialize(response))
                # print('[%s:%d] Marshall response:' % connection.remote_address, response)
                # connection.close()
                    if response is None:
                            print('[%s:%d] Error: response is None' % connection.remote_address)
                    else:
                            print('[%s:%d] Response generated:' % connection.remote_address, response)

                    connection.send(serialize(response))
                    print('[%s:%d] Marshall response:' % connection.remote_address, response)

                except Exception as e:
                    print(f'[Error in {connection.remote_address}]', e)
                    traceback.print_exc()

                finally:
                    connection.close()
                    print('[%s:%d] Close connection' % connection.remote_address)

            case 'error':
                traceback.print_exception(error)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)
    # # foe exercise 4-01
    # def __handle_request(self, request):
    #     try:
    #         # 处理用户数据库相关的请求
    #         if request.name in ['add_user', 'get_user', 'check_password']:
    #             method = getattr(self.__user_db, request.name)
    #             result = method(*request.args)
    #             error = None
    #         # 处理认证服务相关的请求
    #         elif request.name in ['authenticate', 'validate_token']:
    #             method = getattr(self.__auth_service, request.name)
    #             result = method(*request.args)
    #             error = None
    #         else:
    #             raise ValueError(f"Unsupported request name: {request.name}")
    #     except Exception as e:
    #         result = None
    #         error = " ".join(e.args)
    #     return Response(result, error)

    # for exercise 4-02
    # def __handle_request(self, request):
    #         try:
    #             if request.metadata is not None:
    #                 # 验证 token
    #                 if not self.__auth_service.validate_token(request.metadata):
    #                     raise ValueError("Invalid or expired token")
                    
    #             # 用户数据库相关请求由 InMemoryUserDatabase 处理
    #             if request.name in ['add_user', 'get_user', 'check_password']:
    #                 method = getattr(self.__user_db, request.name)
    #                 result = method(*request.args)
    #                 error = None
    #             # 认证相关请求由 InMemoryAuthenticationService 处理
    #             elif request.name in ['authenticate', 'validate_token']:
    #                 method = getattr(self.__auth_service, request.name)
    #                 result = method(*request.args)
    #                 error = None
    #             else:
    #                 raise ValueError(f"Unsupported request name: {request.name}")
    #         except Exception as e:
    #             result = None
    #             error = " ".join(e.args)
    #         return Response(result, error)
    
        # 修改 handle_request 方法，检查角色权限
    def __handle_request(self, request):
        try:
            # 先检查 metadata（Token）是否存在并且有效
            if request.metadata is not None:
                if not isinstance(request.metadata, Token) or not self.__auth_service.validate_token(request.metadata):
                    raise ValueError("Invalid or expired token")

            # 根据 request 的 name 处理不同的请求
            if request.name in ['add_user', 'get_user', 'check_password']:
                method = getattr(self.__user_db, request.name)
                result = method(*request.args)
                error = None
            elif request.name in ['authenticate', 'validate_token']:
                method = getattr(self.__auth_service, request.name)
                result = method(*request.args)
                error = None
            else:
                raise ValueError(f"Unsupported request name: {request.name}")

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
