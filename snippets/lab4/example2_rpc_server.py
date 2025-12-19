from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth_service = InMemoryAuthenticationService(self.__user_db)
        self.__services = (self.__user_db, self.__auth_service)
    
    def __on_connection_event(self, event, connection, address, error):
        if event == 'listen':
            print('Server listening on %s:%d' % address)

        elif event == 'connect':
            connection.callback = self.__on_message_event

        elif event == 'error':
            traceback.print_exception(error)

        elif event == 'stop':
            print('Server stopped')

    
    def __on_message_event(self, event, payload, connection, error):
        if event == 'message':
            print('[%s:%d] Open connection' % connection.remote_address)

            request = deserialize(payload)
            assert isinstance(request, Request)

            print('[%s:%d] Unmarshall request:' % connection.remote_address, request)

            response = self.__handle_request(request)
            connection.send(serialize(response))

            print('[%s:%d] Marshall response:' % connection.remote_address, response)
            connection.close()

        elif event == 'error':
            traceback.print_exception(error)

        elif event == 'close':
            print('[%s:%d] Close connection' % connection.remote_address)

    
    def __handle_request(self, request):
        try:
            method = None
            for service in self.__services:
                if hasattr(service, request.name):
                    method = getattr(service, request.name)
                    break
            if method is None:
                raise AttributeError(f"Unknown RPC method: {request.name}")
            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = str(e) or repr(e)
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
