import argparse
from snippets.lab3 import Server
from snippets.lab4.users import Role, User
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    def __init__(self, port: int, admin_user: User):
        super().__init__(port, self.__on_connection_event)
        assert admin_user.role == Role.ADMIN, "admin_user has to be an ADMIN"
        self.__user_db = InMemoryUserDatabase()
        self.__user_db.add_user(admin_user)
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
    
    def __handle_request(self, request: Request):
        try:
            category, name = request.name.split("/")
            match category:
                case "db":
                    if request.token is None or not self.__auth_service.validate_token(request.token):
                        raise ValueError("Unauthenticated")
                    if request.token.user.role != Role.ADMIN:
                        raise ValueError("Unauthorized")
                    method = getattr(self.__user_db, name)
                    result = method(*request.args)
                case "auth": 
                    method = getattr(self.__auth_service, name)
                    result = method(*request.args)
                case _: 
                    raise ValueError("Invalid category")
                
            error = None
        except Exception as e:
            result = None
            error = " ".join(e.args)
        return Response(result, error)


admin_user = User(
    username="admin",
    emails={"admin@mail.com"}, 
    full_name="Admin", 
    role=Role.ADMIN,  
    password="admin", 
)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int)
    parser.add_argument('--admin-user', '-u', help='Username of the initial admin user')
    parser.add_argument('--admin-email', '--address', '-a', nargs='+', help='Email address of the initial admin user')
    parser.add_argument('--admin-name', '-n', help='Full name of the initial admin user')
    parser.add_argument('--admin-password', '-p', help='Password of the initial admin user')
    args = parser.parse_args()
    user = User(
        username=args.admin_user,
        emails=set(args.admin_email), 
        full_name=args.admin_name, 
        password=args.admin_password, 
        role=Role.ADMIN,
    )
    server = ServerStub(args.port, admin_user)
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
