import os
from snippets.lab3 import Server
from snippets.lab4.users.impl import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


def read_file(file):
    file_path = f"{file}.txt"
    if not os.path.exists(file_path):
        return False
    with open(file_path, "r") as f:
        return f.read()

def write_file(file, content):
    with open(f"{file}.txt", "w") as f:
        f.write(content)


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__user_auth = InMemoryAuthenticationService(self.__user_db)

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
            if(request.name == 'validate_token'):
                token = request.args[0]
                token_content = read_file(token.user.username)
                if not token_content:
                    raise ValueError("Token not found")
                token = deserialize(token_content)
                return Response(self.__user_auth.validate_token(token), None)

            if(request.name == 'authenticate'):
                token = self.__user_auth.authenticate(*request.args)
                write_file(token.user.username, serialize(token))
                return Response(token, None)

            if (request.name in dir(UserDatabase)):
                method = getattr(self.__user_db, request.name)
            elif (request.name in dir(AuthenticationService)):
                method = getattr(self.__user_auth, request.name)
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
