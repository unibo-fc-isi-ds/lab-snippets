from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from snippets.lab4.users import Role
from .users.impl import remove_tokens_in_file
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
        if hasattr(self.__user_db, request.name):
            service_instance = self.__user_db
            if request.name == 'get_user':
                if request.metadata is None:
                    return Response(None, f"Method '{request.name}' need to have a token as an argument.")
                    
                if not self.__auth_service.validate_token(request.metadata):
                    return Response(None, f"Method '{request.name}' the token passed from command line is not valid.")
                if request.metadata.user.role != Role['ADMIN']:
                    token_same_of_requested_user = False
                    if request.args and request.args[0] in request.metadata.user.ids: 
                        token_same_of_requested_user = True
                    if not token_same_of_requested_user:
                        return Response(None, f"A common USER can not get information of a different user.")
        elif hasattr(self.__auth_service, request.name):
            service_instance = self.__auth_service
        else:
            return Response(None, f"Method '{request.name}' not found in available services.")
        try:
            method = getattr(service_instance, request.name)
            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = " ".join(e.args)
        return Response(result, error)


if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    remove_tokens_in_file()
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
