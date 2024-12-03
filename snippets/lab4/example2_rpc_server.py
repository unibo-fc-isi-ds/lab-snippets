from .users import Token, Role
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
        message_db_error   = ""
        message_auth_error = ""
        error = ""

        if request.name == "get_user":
            if not isinstance(request.metadata, tuple) and not request.metadata:
                error = None
                return Response(error, "Fatal Error")
            if not isinstance(request.metadata[0], Token):
                error = None
                return Response(error, "Token was not provided")
            token = request.metadata[0]
            if not self.__auth_service.validate_token(token):
                error = None
                return Response(error, "Token is not valid")
            user =  self.__user_db.get_user(token.user.username)
                
            if user.role.value != Role.ADMIN.value:    
                error = None
                return Response(error, "User not authorized to carry out the operation")

        try:
            method = getattr(self.__user_db, request.name)
            result = method(*request.args)
            error = None
        except AttributeError as e:
            message_db_error = " ".join(e.args)
        except Exception as e:
            result = None
            error = " ".join(e.args)

        try:
            method = getattr(self.__auth_service, request.name)
            result = method(*request.args)
            error = None
        except AttributeError as e:
            message_auth_error = " ".join(e.args)
        except Exception as e:
            result = None
            error = " ".join(e.args)

        if message_db_error and message_auth_error:
            error = "db:"+ message_db_error + "\nauth:" + message_auth_error


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
