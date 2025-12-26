from pathlib import Path
from .example3_rpc_client import *
import argparse
import sys

token_filename = 'token.json'
token: Token | None = None

def token_local_retrieval(path: str) -> Token | None:
    try:
        return deserialize(Path(path).read_text())
    except Exception:
        print(f'Unable to READ token from \"{path}\"')
        return None

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
    parser.add_argument('--token', '-t', help='Path to token file', default=token_filename)

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    session = Session(args.address)
    user_db = RemoteUserDatabase(session)
    auth_service = RemoteAuthenticationService(session)

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        if args.token:
            token_filename = args.token
        token = token_local_retrieval(token_filename)
        if token:
            session.set_token(token)
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
            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                token = auth_service.authenticate(credentials)
                try:
                    Path(token_filename).write_text(serialize(token))
                    print(f'Token saved to \"{token_filename}\"')
                except Exception as e:
                    print(f'Unable to SAVE token to \"{token_filename}\"')
            case 'validate_token':
                if not token:
                    raise ValueError("Token is required")
                print(auth_service.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
