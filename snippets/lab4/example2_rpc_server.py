from snippets.lab3 import Server
from snippets.lab4.users import Role
from snippets.lab4.users.impl import InMemoryAuthenticationService, InMemoryUserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.Auth = InMemoryAuthenticationService(self.__user_db)
    
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
        result = None
        error = None
        try:
            if request.name == 'get_user':
                if not request.metadata:
                    error = "Missing metadata(token). You must be authenticated to use this method"
                elif not self.Auth.validate_token(request.metadata):
                    error = "You are not authenticated"
                elif request.metadata.user.role != Role.ADMIN:
                     error = "You don't have admin role"
                else:
                    result = self.__user_db.get_user(*request.args)
            elif request.name in ['authenticate', 'validate_token']:
                result = getattr(self.Auth, request.name)(*request.args)
            elif request.name in ['check_password', 'add_user']:
                result = getattr(self.__user_db, request.name)(*request.args)
            else:
                error = f"Method {request.name} not found"
        except Exception as e:
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
