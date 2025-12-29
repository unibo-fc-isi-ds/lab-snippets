from .example3_rpc_client import *
import argparse
import sys


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate', 'validate_token'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token-file', '-t', help='Token file (defaults to "token.json")')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    def load_token(token_file: str) -> Token | None:
        token = None
        try:
            with open(token_file, 'r') as f:
                token_serialized = f.read()
                token = deserialize(token_serialized)
                user_db.set_token(token)
                print(f'Token loaded from {token_file}')
        except FileNotFoundError:
            print(f'Token file {token_file} not found')
        return token

    cached_token = load_token(args.token_file or 'token.json')

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
                if not args.role:
                    args.role = 'user'
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                credentials = Credentials(ids[0], args.password)
                token = auth_service.authenticate(credentials)
                token_serialized = serialize(token)
                with open('token.json', 'w') as f:
                    f.write(token_serialized)
                print('Token generated and saved to token.json')
            case 'validate_token':
                token_file = args.token_file or 'token.json'
                token = cached_token if cached_token else load_token(token_file)
                print(auth_service.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
