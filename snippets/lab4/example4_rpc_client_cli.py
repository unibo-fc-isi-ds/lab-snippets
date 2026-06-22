from .example3_rpc_client import *
import argparse
import sys
from pathlib import Path

TOKEN_FILE = Path.home() / ".lab4_token.json"

def load_token() -> Token | None:
    try:
        with open(TOKEN_FILE) as f:
            return deserialize(f.read())
    except FileNotFoundError:
        return None

def save_token(token: Token):
    with open(TOKEN_FILE, "w") as f:
        f.write(serialize(token))
    print("Token saved to", TOKEN_FILE)



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
    parser.add_argument('--duration', '-d', help='Authentication token duration')
    parser.add_argument('--token', '-t', help='Authentication token')
    

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)
    
    token = load_token()
    if token:
        user_db._token = token
        auth_service._token = token

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
                print(user_db.get_user(ids[0], metadata=token))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials, metadata=token))
            case 'authenticate':
                credentials = Credentials(ids[0], args.password)
                if not args.duration:
                    duration = None
                else:
                    duration = timedelta(milliseconds=int(args.duration))
                token = auth_service.authenticate(credentials, duration)
                save_token(token)
                user_db.current_token = token
                auth_service.current_token = token
            case 'validate':
                if not args.token:
                    raise ValueError("Token is required for validation")
                token_obj = deserialize(args.token) 
                is_valid = auth_service.validate_token(token_obj)
                print("Valid token" if is_valid else "Invalid token")
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
