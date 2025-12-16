from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from snippets.lab4.users import Role
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
    
    def __handle_request(self, request):
        try:
            if hasattr(self.__user_db, request.name):
                target = self.__user_db
            elif hasattr(self.__auth_service, request.name):
                target = self.__auth_service
            else:
                return Response(None, f"Method {request.name} not defined")
            secure_methods = ['get_user']
            if request.name in secure_methods:
                token = request.metadata.get('token')
                if not token or not self.__auth_service.validate_token(token):
                    raise PermissionError("Unauthorized: invalid or missing token")
                if token.user.role != Role.ADMIN:
                    raise PermissionError("Forbidden: Only ADMIN users can perform this action")
            method = getattr(target, request.name)
            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            traceback.print_exc() 
            error = " ".join(str(arg) for arg in e.args)
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
