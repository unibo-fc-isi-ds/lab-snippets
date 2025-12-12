from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryAuthenticationService, InMemoryUserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback

class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth = InMemoryAuthenticationService(self.__user_db)

    def __on_connection_event(self, event, connection, address, error):
        match event:
            case 'listen':
                print(f'Server listening on {address[0]}:{address[1]}')
            case 'connect':
                connection.callback = self.__on_message_event
            case 'error':
                traceback.print_exception(error)
            case 'stop':
                print('Server stopped')

    def __on_message_event(self, event, payload, connection, error):
        match event:
            case 'message':
                print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Open connection')
                request = deserialize(payload)
                assert isinstance(request, Request)
                print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Unmarshalled request:', request)
                response = self.__handle_request(request)
                serialized = serialize(response)
                connection.send(serialized)
                print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Marshalled response:', response)
                # Assicurati di chiudere solo dopo aver inviato tutto
                connection.close()
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Close connection')

    def __handle_request(self, request):
        try:
            # Cerca il metodo su auth prima, poi su user_db
            if hasattr(self.__auth, request.name):
                method = getattr(self.__auth, request.name)
            elif hasattr(self.__user_db, request.name):
                method = getattr(self.__user_db, request.name)
            else:
                raise AttributeError(f"Method {request.name} not found")
            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = " ".join(str(a) for a in e.args) or str(e)
        return Response(result, error)


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1])
    server = ServerStub(port)
    print(f'Started server on port {port}')
    try:
        while True:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
    except (EOFError, KeyboardInterrupt):
        pass
    server.close()
