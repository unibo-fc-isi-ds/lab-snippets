import os
from .example3_rpc_client import *
import argparse
import sys

TOKEN_FILE = 'auth_token.json'

def save_token_to_file(token: Token, filename: str = TOKEN_FILE):
    with open(filename, 'w') as f:
        f.write(serialize(token))

def load_token_from_file(filename: str = TOKEN_FILE) -> Token:
    if not os.path.exists(filename):
        raise FileNotFoundError(f"Token file '{filename}' not found")
    with open(filename, 'r') as f:
        token_str = f.read()
    return deserialize(token_str)


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method call', choices=['add', 'get', 'check', 'authenticate', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token', '-t', help='Serialized token string')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    cached_token = load_token_from_file() if os.path.exists(TOKEN_FILE) else None
    if cached_token:
        user_db.set_access_token(cached_token)
        print(f"Loaded session for user: {cached_token.user.username}")

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
                role_name = args.role.upper() if args.role else 'USER'
                role_enum = Role[role_name]
                user = User(args.user, args.email, args.name, role_enum, args.password)
                print(user_db.add_user(user))
            case 'authenticate':
                if not args.password or (not args.user and not args.email):
                    raise ValueError("Username or email and password are required")
                credentials = Credentials(args.user, args.password)
                token = auth_service.authenticate(credentials)
                save_token_to_file(token)
                print('Serialized token:', serialize(token))
            case 'validate':
                token = None
                if args.user or args.email and args.password:
                    auth_ids = (args.email or []) + [args.user]
                    credentials = Credentials(auth_ids[0], args.password)
                    token = auth_service.authenticate(credentials)
                elif cached_token:
                    print('Using cached token for validation')
                    token = cached_token
                else:
                    raise ValueError("Either username/email and password or a cached token is required for validation")
                print('Validating token:', token, ' ...')
                is_valid = auth_service.validate_token(token)
                if is_valid:
                    print('Token is valid')
                else:
                    print('Token is invalid or expired')
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
