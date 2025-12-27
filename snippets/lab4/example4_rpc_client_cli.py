from .example3_rpc_client import *
import argparse
import sys
import json 
from pathlib import Path 

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check','authenticate','validate'])
    parser.add_argument('--as-user',help= 'Executing command as user')
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)
    caller = args.as_user
    TOKEN_FILE = Path.home() / f".rpc_token_{caller}.json"

    def save_token(token):
        with TOKEN_FILE.open("w") as f:
            f.write(serialize(token))

    def load_token():
        if TOKEN_FILE.exists():
            with TOKEN_FILE.open() as f:
                return deserialize(f.read())
        return None
    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)
    prev_token = load_token()
    if prev_token:
        user_db._token = prev_token
        auth_service._token = prev_token

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
                if not args.as_user:
                    raise ValueError("--as-user is required to identify the caller")
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                if not args.as_user:
                    raise ValueError("--as-user is required to identify the caller")
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                token = auth_service.authenticate(credentials)
                user_db._token = token
                save_token(token)
            case 'validate':
                print(auth_service.validate_token(user_db._token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
