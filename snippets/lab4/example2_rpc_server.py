from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from snippets.lab4.users.cryptography import DefaultSigner
from snippets.lab4.users import Role
import traceback

TEST_SECRET = 'secret'

class ServerStub(Server):
    def __init__(self, port, debug=False):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase(debug)
        self.__auth_service = \
            InMemoryAuthenticationService(self.__user_db) if not debug else \
            InMemoryAuthenticationService(self.__user_db, DefaultSigner(TEST_SECRET))    
        self.__protected_operations = {'get_user', 'check_password'}
        
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
    
    def __handle_request(self, request: Request):
        try:
            if request.service == 'database':
                if request.name in self.__protected_operations:
                    if request.token is None:
                        raise Exception('Bad request: protected operation called with no authentication token provided')
                    validation_result = self.__auth_service.validate_token(token=request.token)
                    if not validation_result:
                        raise Exception('Bad request: protected operation called with invalid token provided')
                    admin_user = self.__user_db.get_user(id=request.token.user.username)
                    if admin_user.role is not Role.ADMIN:
                        raise Exception('Bad request: protected operation called by unauthorized user')
                method = getattr(self.__user_db, request.name)
            elif request.service == 'authentication':
                method = getattr(self.__auth_service, request.name)
            else:
                raise Exception('Bad Request: no valid service called')
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