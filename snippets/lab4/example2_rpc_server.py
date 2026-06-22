from snippets.lab3 import Server
from snippets.lab4.users import Credentials, Role, User
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__user_db.add_user(User(username='alice', emails=['alice@test.com'], full_name='Alice', role=Role.USER, password='alice'))
        self.__user_db.add_user(User(username='bob', emails=['bob@test.com'], full_name='Bob', role=Role.USER, password='bob'))

        self.__auth_service = InMemoryAuthenticationService(self.__user_db)
        #self._user.get_user('alice')
        #self._user.get_user('bob')
        #self._user.check_password('alice', 'alice')
        #self._user.check_password('bob', 'bob')
    
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
        #request.name = get_user | add_user | check_password
        try:
            if request.name == 'authenticate':
                result = self.__auth_service.authenticate(credentials=request.args[0])
                error = None
            else:
                method = getattr(self.__user_db, request.name) #getattr accetta due argomenti: un oggetto e una stringa. Se
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
