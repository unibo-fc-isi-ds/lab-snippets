from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.users import User, Role
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
from typing import List
import traceback


class ServerStub(Server):
    def __init__(self, port, users: List[User] = []):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth_service = InMemoryAuthenticationService(self.__user_db, debug=True)
        for user in users:
            self.__user_db.add_user(user)
        
    
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
            if hasattr(self.__auth_service, request.name): # Checks if the method exists in the authentication service
                method = getattr(self.__auth_service, request.name)
            elif hasattr(self.__user_db, request.name) and 'token' in request.metadata: # Checks if the method exists in the user database and if the token is present
                if request.metadata['token'] is None:
                    raise ValueError("Token is required")
                elif self.__auth_service.validate_token(request.metadata['token']): # Checks if the token is valid
                    if request.name in ["get_user", "check_password"] and request.metadata['token'].user.role != Role.ADMIN:
                        raise ValueError("Only admins can get user information")
                    elif request.name in ["add_user"] and (request.metadata['token'].user.role != Role.ADMIN and request.args[0].role == Role.ADMIN):
                        raise ValueError("Only admins can add other admins")
                    method = getattr(self.__user_db, request.name)
                else:
                    raise ValueError("Invalid token")
            else:
                raise ValueError(f"Unsupported method {request.name}") 
            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = " ".join(e.args)
        return Response(result, error)


if __name__ == '__main__':
    import sys
    # Default admin user
    admin = User(username="admin", emails={"admin@mail.com"}, full_name="Admin", role=Role.ADMIN, password="qwerty1234")
    
    server = ServerStub(int(sys.argv[1]), [admin])
    while True:
        try:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
        except (EOFError, KeyboardInterrupt):
            break
    server.close()
