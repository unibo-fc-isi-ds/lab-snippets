from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback
from .users import Token, Role


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth_srvc = InMemoryAuthenticationService(self.__user_db)

    
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
        error = ""
        auth_error = ""
        user_db_error = ""

        if request.name == "get_user":
            try:
                isinstance(*request.metadata, Token)
            except Exception as e:
                result = None
                return Response(result, "Missing authentication token.")
            if not self.__auth_srvc.validate_token(*request.metadata):
                result = None
                return Response(result, "Request not allowed. Authentication required.")
            user = self.__user_db.get_user((request.metadata[0]).user.username)
            if user.role != Role.ADMIN:
                result = None
                return Response(result, "Request not allowed. User is not authorized.")
        
        try:
            method = getattr(self.__auth_srvc, request.name)
            result = method(*request.args)
            error = None
        except AttributeError as ae:
            auth_error = " ".join(ae.args)
        except Exception as e:
            result = None
            error = " ".join(e.args)

        try:
            method = getattr(self.__user_db, request.name)
            result = method(*request.args)
            error = None
        except AttributeError as ae:
            user_db_error = " ".join(ae.args)
        except Exception as e:
            result = None
            error = " ".join(e.args)

        if auth_error != "" and user_db_error != "":
            error = auth_error + "\n" + user_db_error

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
