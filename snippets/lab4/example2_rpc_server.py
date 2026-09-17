# server.py
from snippets.lab3 import Server
from datetime import timedelta, datetime
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth = InMemoryAuthenticationService(self.__user_db)

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
                print('[%s:%d] Unmarshall request:' %
                      connection.remote_address, request)
                response = self.__handle_request(request)
                connection.send(serialize(response))
                print('[%s:%d] Marshall response:' %
                      connection.remote_address, response)
                connection.close()
            case 'error':
                traceback.print_exception(error)
            case 'close':
                print('[%s:%d] Close connection' % connection.remote_address)

    def __handle_request(self, request):
        try:
            # Check authorization for get_user - only admin users can read
            if request.name == "get_user":
                if len(request.args) < 2:
                    raise ValueError("get_user requires a user ID and a token for authorization")
                user_id = request.args[0]
                token_data = request.args[1]
                
                # Convert token from dict to Token object if needed
                from snippets.lab4.users import Token, User, Role
                if isinstance(token_data, dict):
                    # Token was serialized as dict (backward compatibility)
                    token = Token(
                        user=User(
                            username=token_data["user"]["username"],
                            emails=set(token_data["user"]["emails"]),
                            full_name=token_data["user"]["full_name"],
                            role=Role[token_data["user"]["role"]],
                            password=None
                        ),
                        expiration=datetime.fromisoformat(token_data["expiration"]),
                        signature=token_data["signature"]
                    )
                else:
                    token = token_data
                
                # Validate token
                if not self.__auth.validate_token(token):
                    raise ValueError("Invalid or expired token")
                
                # Check if user is admin
                if token.user.role.name != "ADMIN":
                    raise ValueError("Only admin users can read user data")
                
                # Call get_user with just the user_id
                result = self.__user_db.get_user(user_id)
            elif hasattr(self.__user_db, request.name):
                method = getattr(self.__user_db, request.name)
                args = list(request.args)
                result = method(*args)
            elif hasattr(self.__auth, request.name):
                method = getattr(self.__auth, request.name)
                args = list(request.args)
                if request.name == "authenticate" and len(args) > 1:
                    if args[1] is not None:
                        args[1] = timedelta(seconds=int(args[1]))
                result = method(*args)
            else:
                raise AttributeError(f"Unknown RPC method '{request.name}'")

            # --- PATCH: convert Token to dict to make it serializable ---
            from snippets.lab4.users import Token
            if isinstance(result, Token):
                result = {
                    "user": {
                        "username": result.user.username,
                        "emails": list(result.user.emails),
                        "full_name": result.user.full_name,
                        "role": result.user.role.name
                    },
                    "expiration": result.expiration.isoformat(),
                    "signature": result.signature
                }

            error = None

        except Exception as e:
            result = None
            error = " ".join(map(str, e.args))

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
