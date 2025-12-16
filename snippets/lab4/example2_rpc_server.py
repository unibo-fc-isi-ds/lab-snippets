from snippets.lab3 import Server
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
                print('Server listening on address {address}'.format(address=address))
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
                print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Unmarshall request:', request)
                response = self.__handle_request(request)
                serialized_response = serialize(response)
                connection.send(serialized_response)
                print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Sent response:', response)
                connection.close()
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print(f'[{connection.remote_address[0]}:{connection.remote_address[1]}] Close connection')
    
    def __handle_request(self, request):
        try:
            if hasattr(self.__auth_service, request.name):
                method = getattr(self.__auth_service, request.name)
            elif hasattr(self.__user_db, request.name):
                method = getattr(self.__user_db, request.name)
            else:
                raise ValueError(f"Unsupported method {request.name}")
            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = str(e)
        return Response(result, error)


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1])
    server = ServerStub(port)
    print('Server started on port', port)
    try:
        while True:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
    except (EOFError, KeyboardInterrupt):
        pass
    server.close()
