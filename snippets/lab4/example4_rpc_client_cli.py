from .example3_rpc_client import *
import argparse
import sys

TOKEN_FILE = './token'

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'auth', 'token'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--duration', '-d', help='Token Duration')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    client_stub = ClientStubFull(args.address)

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
                if args.role == None:
                    args.role = Role.USER
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(client_stub.remote.add_user(user))
            case 'get':
                try:
                    with open(TOKEN_FILE + ids[0] + '.json', 'r') as f:
                        token = deserialize(f.read())
                    print(client_stub.remote.get_user(ids[0], token))
                except FileNotFoundError as e:
                    print("The user is not authenticated!")
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(client_stub.remote.check_password(credentials))
            case 'auth':
                credentials = Credentials(ids[0], args.password)
                duration = timedelta(days=int(args.duration)) if args.duration != None else None
                token = client_stub.auth.authenticate(credentials, duration)
                if isinstance(token, Token):
                    with open(TOKEN_FILE + ids[0] + '.json', 'w') as f:
                        f.write(serialize(token))
                print(token)
            case 'token':
                try:
                    with open(TOKEN_FILE + ids[0] + '.json', 'r') as f:
                        print(client_stub.auth.validate_token(deserialize(f.read())))
                except FileNotFoundError as e:
                    print("The user is not valid!")
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
