from .example3_rpc_client import *
import argparse
import sys
from datetime import timedelta

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database and authentication service',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call',
                        choices=['add', 'get', 'check', 'authenticate', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--duration', '-d', type=int, help='Token duration in seconds')
    parser.add_argument('--token', '-t', help='Path to JSON file containing the token')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

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
                print(f"Token: {serialize(token)}")

            case 'validate':
                if not args.token:
                    raise ValueError("Token file path is required (use --token flag with path to JSON file)")
                try:
                    with open(args.token, 'r', encoding='utf-8') as f:
                        token_json = f.read()
                except OSError as e:
                    raise ValueError(f"Cannot read token file: {e}")
                token = deserialize(token_json)
                if not isinstance(token, Token):
                    raise ValueError("Invalid token format")
                result = auth_service.validate_token(token)
                print(f"Token is {'valid' if result else 'invalid'}")

            case _:
                raise ValueError(f"Invalid command '{args.command}'")

    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
    except ValueError as e:
        print(f'[{type(e).__name__}]', *e.args)