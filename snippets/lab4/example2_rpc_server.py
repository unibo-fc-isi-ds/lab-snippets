from snippets.lab3 import Server
from snippets.lab4.users import Role
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth_service = InMemoryAuthenticationService(self.__user_db)
        self.__routes = {
            "add_user": {"method": self.__user_db.add_user, "auth_required": False},
            "get_user": {"method": self.__user_db.get_user, "auth_required": True, "admin_required": True},
            "check_password": {"method": self.__user_db.check_password, "auth_required": False},
            "authenticate": {"method": self.__auth_service.authenticate, "auth_required": False},
            "validate_token": {"method": self.__auth_service.validate_token, "auth_required": False},
        }
    
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
            route = self.__routes.get(request.name)
            method = route.get('method')
            
            auth_required = route.get("auth_required", False)
            admin_required = route.get("admin_required", False)
            
            if auth_required:
                token = request.metadata
                if(token is None):
                    raise PermissionError("Authentication token required")
                if not self.__auth_service.validate_token(token):
                    raise PermissionError("Invalid token")
                if admin_required and token.user.role != Role.ADMIN:
                    raise PermissionError("Admin role required")  
            
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
