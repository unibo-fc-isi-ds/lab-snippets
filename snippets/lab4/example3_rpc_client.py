from snippets.lab3 import Client, address
from snippets.lab4.users import *
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub(Client):
    def __init__(self, server_address):
        super().__init__(server_address)
        print('# Connected to %s:%d' % self.remote_address)
    
    def rpc(self, name, *args):
        request = Request(name, args)
        print('# Marshalling', request, 'towards', "%s:%d" % self.remote_address)
        request = serialize(request)
        print('# Sending message:', request.replace('\n', '\n# '))
        self.send(request)
        response = self.receive()
        print('# Received message:', response.replace('\n', '\n# '))
        response = deserialize(response)
        assert isinstance(response, Response)
        print('# Unmarshalled', response, 'from', "%s:%d" % self.remote_address)
        if response.error:
            raise RuntimeError(response.error)
        return response.result
    
    def close(self):
        super().close()
        print('# Disconnected from %s:%d' % self.remote_address)


class RemoteUserDatabase(ClientStub, UserDatabase):
    def __init__(self, server_address):
        super().__init__(server_address)
    
    def add_user(self, user: User):
        return self.rpc('add_user', user)
    
    def get_user(self, id: str) -> User:
        return self.rpc('get_user', id)
    
    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)
    

if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='RPC client for user database')
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')

    args = parser.parse_args()
    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
    finally:
        user_db.close()
