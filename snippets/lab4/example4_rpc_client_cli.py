from .example3_rpc_client import *
import argparse
import sys
import json
from pathlib import Path

TOKEN_FILE = Path.cwd() / "token.json"

def save_token(token):
    try:
        with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
            f.write(serialize(token))
        print("Token saved")
    except Exception as e:
        print(f"Failed to save token: {e}")

def load_token():
    if TOKEN_FILE.exists():
        content = TOKEN_FILE.read_text(encoding='utf-8').strip()
        if not content:
            print("Token file is empty")
            return None
        try:
            return deserialize(content)
        except Exception as e:
            print(f"Failed to load token: {e}")
            return None
    return None

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'auth'])
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

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_client = RemoteAuthenticationService(args.address)
    saved_token = load_token()

    if saved_token:
        auth_client.set_token(saved_token)
        user_db.set_token(saved_token)
        print("Loaded saved token")

    try:
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        match args.command:
            case 'auth':
                if not args.user or not args.password:
                    raise ValueError("Username and password are required for authentication")
                credentials = Credentials(args.user, args.password)
                token = auth_client.authenticate(credentials)
                save_token(token)
                print(f"Authentication token: {token}")
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
