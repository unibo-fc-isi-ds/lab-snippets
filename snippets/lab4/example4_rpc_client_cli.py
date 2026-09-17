from pathlib import Path
from .example3_rpc_client import *
import argparse
import sys

_TOKEN_PATH = 'token.json'
token: Token | None = None

def get_token(path: str) -> Token | None:
    token = None
    try:
        with open(path, 'r') as f:
            token_serialized = f.read()
        token = deserialize(token_serialized)
        print(f'Token READ from "{Path(f.name).resolve()}"')
    except Exception as e:
        print(f'Unable to READ token from "{path}"')
    return token

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token', '-t', help=f'Token path (defaults "{_TOKEN_PATH}")')
    parser.add_argument('--days', '-d', help='Token validity in days (defaults to 1 day)')
    parser.add_argument('--seconds', '-s', help='Token validity in seconds (defaults to 1 day)')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    try:
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        tokenPath = _TOKEN_PATH
        if args.token:
            tokenPath = args.token
        token = get_token(tokenPath)
        if token:
            user_db.token = token
            auth_service.token = token
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                if not args.role:
                    args.role = "user"
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                credentials = Credentials(ids[0], args.password)
                if args.days:
                    token = auth_service.authenticate(credentials, timedelta(days=float(args.days)))
                elif args.seconds:
                    token = auth_service.authenticate(credentials, timedelta(seconds=float(args.seconds)))
                else:
                    token = auth_service.authenticate(credentials)
                token_serialized = serialize(token)
                try:
                    with open(tokenPath, 'w') as f:
                        f.write(token_serialized)
                    print(f'Token WROTE in "{Path(f.name).resolve()}"')
                except Exception as e:
                    print(f'Error while saving token in "{tokenPath}"', file=sys.stderr)
            case 'validate':
                if token:
                    print(auth_service.validate_token(token))
                else:
                    print("Impossible to validate without a token", file=sys.stderr)
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
