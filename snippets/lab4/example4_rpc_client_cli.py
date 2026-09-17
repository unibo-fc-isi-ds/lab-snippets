from .example3_rpc_client import *
import argparse
import sys
from datetime import timedelta
import os

DEFAULT_TOKEN_FILE = '.rpc_token.json'

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='Secure RPC client for user database and authentication service',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call',
                        choices=['add', 'get', 'check', 'authenticate', 'validate', 'logout'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--duration', '-d', type=int, help='Token duration in seconds')
    parser.add_argument('--token', '-t', help='Path to token file (default: .rpc_token.json)')
    parser.add_argument('--no-save', action='store_true', help='Do not save token to file after authentication')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    token_file = args.token if args.token else DEFAULT_TOKEN_FILE

    def load_token_from_file(filepath):
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r', encoding='utf-8') as f:
                    token_json = f.read()
                token = deserialize(token_json)
                if not isinstance(token, Token):
                    return None
                user_db.set_token(token)
                return token
            return None
        except Exception:
            return None

    def save_token_to_file(token, filepath):
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(serialize(token))
            return True
        except Exception as e:
            print(f"Warning: Could not save token to file: {e}")
            return False

    if args.command not in ['authenticate', 'add', 'check']:
        existing_token = load_token_from_file(token_file)
        if existing_token:
            print(f"Loaded existing token from {token_file}")

    try:
        ids = (args.email or []) + ([args.user] if args.user else [])

        match args.command:
            case 'add':
                if len(ids) == 0:
                    raise ValueError("Username or email address is required")
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                role = Role[args.role.upper()] if args.role else Role.USER
                user = User(args.user, set(args.email or []), args.name, role, args.password)
                result = user_db.add_user(user)
                print(f"User added successfully")

            case 'get':
                if len(ids) == 0:
                    raise ValueError("Username or email address is required")

                current_token = user_db.get_token()
                if not current_token:
                    print("ERROR: No authentication token available.")
                    print(f"Please authenticate first or provide token file with --token flag")
                    sys.exit(1)

                user = user_db.get_user(ids[0])
                print(f"User found: {user}")

            case 'check':
                if len(ids) == 0:
                    raise ValueError("Username or email address is required")
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                result = user_db.check_password(credentials)
                print(f"Credentials are {'correct' if result else 'incorrect'}")

            case 'authenticate':
                if len(ids) == 0:
                    raise ValueError("Username or email address is required")
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                duration = timedelta(seconds=args.duration) if args.duration else None
                token = auth_service.authenticate(credentials, duration)
                print(f"Authentication successful!")

                if not args.no_save:
                    if save_token_to_file(token, token_file):
                        print(f"\nToken saved to: {token_file}")
                    else:
                        print(f"\nToken not saved. Use --token to specify manually in future commands.")
                else:
                    print(f"\nToken not saved (--no-save specified)")
                    print(f"Token JSON:")
                    print(serialize(token))

            case 'validate':
                token = None
                if args.token:
                    token = load_token_from_file(args.token)
                else:
                    token = user_db.get_token()

                if not token:
                    raise ValueError("No token available. Specify --token or authenticate first.")

                result = auth_service.validate_token(token)
                print(f"Token is {'valid' if result else 'invalid'}")

            case 'logout':
                # Clear token file and memory
                user_db.clear_token()
                if os.path.exists(token_file):
                    os.remove(token_file)
                    print(f"Logged out. Token file {token_file} removed.")
                else:
                    print(f"Logged out. No token file found.")

            case _:
                raise ValueError(f"Invalid command '{args.command}'")

    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
    except ValueError as e:
        print(f'[{type(e).__name__}]', *e.args)