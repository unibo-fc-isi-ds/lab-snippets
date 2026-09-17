from .example3_rpc_client import *
import argparse
import sys
import os

TOKEN_PATH = os.path.join(os.path.dirname(__file__), 'token.json')

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'auth', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'], default='user')
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token', '-t', help='Path to token JSON file')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    server_addr = address(args.address)
    user_db = RemoteUserDatabase(server_addr)
    auth = RemoteAuthenticationService(server_addr)

    try:
        match args.command:
            case 'add':
                if not args.user:
                    raise ValueError("Username is required (-u)")
                if not args.email:
                    raise ValueError("Email is required (-a)")
                if not args.password:
                    raise ValueError("Password is required (-p)")
                if not args.name:
                    raise ValueError("Full name is required (-n)")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))

            case 'get':
                if not args.user:
                    raise ValueError("Username is required (-u)")
                token_path = args.token or TOKEN_PATH
                try:
                    with open(token_path, 'r') as f:
                        token_json = f.read()
                except FileNotFoundError:
                    raise ValueError(f"Token file '{token_path}' not found. Run 'auth' first.")
                token = deserialize(token_json)
                user_db.set_token(token)
                print(user_db.get_user(args.user))

            case 'check':
                if not args.user:
                    raise ValueError("Username is required (-u)")
                if not args.password:
                    raise ValueError("Password is required (-p)")
                credentials = Credentials(args.user, args.password)
                print(user_db.check_password(credentials))

            case 'auth':
                if not args.user:
                    raise ValueError("Username is required (-u)")
                if not args.password:
                    raise ValueError("Password is required (-p)")
                credentials = Credentials(args.user, args.password)
                token = auth.authenticate(credentials)
                token_json = serialize(token)
                token_path = args.token or TOKEN_PATH
                with open(token_path, 'w') as f:
                    f.write(token_json)
                print(f"Token saved to {token_path}")

            case 'validate':
                token_path = args.token or TOKEN_PATH
                try:
                    with open(token_path, 'r') as f:
                        token_json = f.read()
                except FileNotFoundError:
                    raise ValueError(f"Token file '{token_path}' not found. Run 'auth' first.")
                token = deserialize(token_json)
                print(auth.validate_token(token))

            case _:
                raise ValueError(f"Invalid command '{args.command}'")

    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
    except Exception as e:
        print(f'[{type(e).__name__}]', str(e))
