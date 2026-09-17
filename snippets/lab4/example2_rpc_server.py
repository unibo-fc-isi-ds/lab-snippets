from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from snippets.lab4.users import Role
from datetime import timedelta
import traceback


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__user_auth = InMemoryAuthenticationService(database=self.__user_db)
    
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
            name = request.name
            if name.startswith("user."):
                if name == 'user.get_user':
                    if request.metadata is None:
                        return Response(None, f"Token needed for {name} operations")
                    if not self.__user_auth.validate_token(request.metadata):
                        return Response(None, "Authorization FAILED: Token not valid") 
                    if request.metadata.user.role != Role.ADMIN:
                        return Response(None, f"Authorization FAILED: Role not valid for {name} operations")
                method = getattr(self.__user_db, name[len("user."):])
            elif name.startswith("auth."):
                method = getattr(self.__user_auth, name[len("auth."):])
                if name == 'auth.authenticate' and len(request.args) > 1:
                    credentials, duration = request.args
                    if isinstance(duration, (int, float)):
                        duration = timedelta(seconds=duration)
                    request.args = (credentials, duration)
            else:
                raise ValueError(f"Unknown service for {name}")
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
