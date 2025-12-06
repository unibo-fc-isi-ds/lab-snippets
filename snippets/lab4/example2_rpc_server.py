from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from .users.auth_impl import InMemoryAuthenticationService
import traceback

class AuthenticationServerStub:
    def __init__(self, auth_service: InMemoryAuthenticationService):
        self.auth_service = auth_service

    def handle_request(self, request):
        try:
            if request.name == "authenticate":
                credentials, duration = request.args
                result = self.auth_service.authenticate(credentials, duration)
                error = None
            elif request.name == "validate_token":
                token, = request.args
                result = self.auth_service.validate_token(token)
                error = None
            else:
                result = None
                error = f"Unknown method: {request.name}"
        except Exception as e:
            result = None
            error = " ".join(e.args)
        return Response(result, error)


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.auth_service = InMemoryAuthenticationService(self.__user_db)
        self.auth_stub = AuthenticationServerStub(self.auth_service)
    
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
        # Разделяем UserDB и Auth запросы
        if request.name in ["add_user", "get_user", "check_password"]:
            try:
                method = getattr(self.__user_db, request.name)
                result = method(*request.args)
                error = None
            except Exception as e:
                result = None
                error = str(e)
        elif request.name in ["authenticate", "validate_token"]:
            # AuthService
            return self.auth_stub.handle_request(request)
        else:
            result = None
            error = f"Unknown method: {request.name}"
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
