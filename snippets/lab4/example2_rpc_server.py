from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth_service = InMemoryAuthenticationService(self.__user_db)

    def __check_authorization(self, token: Token):
        if not self.__auth_service.validate_token(token):
            raise PermissionError("Invalid or expired token")
        if token.user.role != Role.ADMIN:
            raise PermissionError("Unauthorized access: only admins can perform this operation")
    
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
        try:
            # Gestione delle richieste
            if request.name == "get_user":
                # Richieste protette da autorizzazione
                token, user_id = request.args
                self.__check_authorization(token)  # Verifica token e ruolo admin
                method = getattr(self.__user_db, request.name)
                result = method(user_id)
            elif request.name in dir(self.__user_db):
                # Operazioni relative al database utenti
                method = getattr(self.__user_db, request.name)
                result = method(*request.args)
            elif request.name in dir(self.__auth_service):
                # Operazioni relative al servizio di autenticazione
                method = getattr(self.__auth_service, request.name)
                result = method(*request.args)
            else:
                # Metodo sconosciuto
                raise ValueError(f"Unknown method '{request.name}'")
            error = None
        except PermissionError as e:
            # Errore di autorizzazione
            result = None
            error = f"PermissionError: {' '.join(e.args)}"
        except Exception as e:
            # Altri errori
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