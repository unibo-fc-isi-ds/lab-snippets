from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase
from snippets.lab4.users.impl import InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from .users import Role
import traceback
from pathlib import Path

TOKEN_FILE = Path.home() / ".lab4_token.json"

def clean_token_file():
    if TOKEN_FILE.exists():
        TOKEN_FILE.unlink()
        print(f"Token file {TOKEN_FILE} removed")
        
class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth = InMemoryAuthenticationService(self.__user_db)
    
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
                protected_methods = ["get_user", "check_password"]
                if request.name in protected_methods:
                    token_obj = request.metadata
                    if token_obj is None:
                        response = Response(None, "Missing token")
                    elif not self.__auth.validate_token(token_obj):
                        response = Response(None, "Invalid token")
                    else:
                        if request.metadata.user.role == Role.ADMIN:
                            response = self.__handle_request(request)
                        else:
                            response = Response(None, "User not authorized")
                else:
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
                method = getattr(self.__user_db, request.name)
            elif hasattr(self.__auth, request.name):
                method = getattr(self.__auth, request.name)
            else:
                raise AttributeError(f"Unknown RPC method: {request.name}")
            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = " ".join(e.args)
        return Response(result, error)


if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    try:
        while True:
            try:
                input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
            except (EOFError, KeyboardInterrupt):
                break
    finally:
        clean_token_file()
        server.close()
