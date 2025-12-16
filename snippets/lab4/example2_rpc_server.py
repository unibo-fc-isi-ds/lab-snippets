from snippets.lab3 import Server
from snippets.lab4.users.impl import InMemoryUserDatabase
from snippets.lab4.users.impl import InMemoryAuthenticationService # New import
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback
import os
import glob

def cleanup_tokens():
    for filename in glob.glob(".token_*"):
        try:
            os.remove(filename)
            print(f"Removed token file: {filename}")
        except Exception as e:
            print(f"Could not remove {filename}: {e}")
# This function is used to clen all the .token files when the server
# has been closed

class ServerStub(Server):
    def __init__(self, port):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        self.__auth_service = InMemoryAuthenticationService(self.__user_db)
        # Creating an InMemoryAuthenticationService instance, this class is contained in the 
        # impl.py file under the "users" folder
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
        # Now the server has to handle two type of service:
        # InMemoryUserDatabase and InMemoryAuthenticationService
        try:
            if hasattr(self.__user_db, request.name):
                method = getattr(self.__user_db, request.name)
            elif hasattr(self.__auth_service, request.name):
                method = getattr(self.__auth_service, request.name) # There the RPC request is
            # delegated to the authtentication service which can return an output like "Invalid credentials"
            # in case of invalid credentials or create a token for the user.
            else:
                raise ValueError(f"{request.name} is not a valid operation")
            result = method(*request.args)
            error = None
        except Exception as e:
            result = None
            error = " ".join(e.args)
        return Response(result, error)
    # So now both service has been provided server side: add_user, get_user, check password (from UserDatabase).
    # And authenticate, validate_token (from AuthenticationService)


if __name__ == '__main__':
    import sys
    server = ServerStub(int(sys.argv[1]))
    try:
        while True:
            input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
    except (EOFError, KeyboardInterrupt):
        pass
    finally:
        print("Cleaning up token files...")
        cleanup_tokens()
        try: # TO avoid windows error in output 
            server.close()
        except OSError:
            pass
