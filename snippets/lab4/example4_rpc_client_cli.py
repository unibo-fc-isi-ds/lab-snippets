from snippets.lab4.example0_users import _PRINT_LOGS
from snippets.lab4.users.impl import InMemoryUserDatabase
from .example3_rpc_client import *
import argparse
import sys


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog='python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address(es)')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'], default='user')
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token', '-t', help='Token string')
    parser.add_argument('--path', '-th', help='Path to token file')

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
        if not ids:
            raise ValueError("At least a username or an email address is required.")

        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required for 'add' command.")
                if not args.name:
                    raise ValueError("Full name is required for 'add' command.")
                user = User(
                    username=args.user,
                    emails=args.email,
                    full_name=args.name,
                    role=Role[args.role.upper()],
                    password=args.password,
                )
                print(user_db.add_user(user))

            case 'get':
                if args.path:
                    with open(args.path, 'r') as file:
                        token = deserialize(file.read().strip())
                else:
                    raise ValueError("Token file path is required for 'get' command.")
                print(user_db.get_user(ids[0], token))

            case 'check':
                if not args.password:
                    raise ValueError("Password is required for 'check' command.")
                credentials = Credentials(id=ids[0], password=args.password)
                print(user_db.check_password(credentials))

            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required for 'authenticate' command.")
                credentials = Credentials(id=ids[0], password=args.password)
                token = auth_service.authenticate(credentials)
                print(f"User '{args.user}' authenticated successfully.")
                if args.path:
                    with open(args.path, 'w') as file:
                        file.write(serialize(token))
                    print(f"Token saved to {args.path}")
                print(token)

            case 'validate':
                if args.token and args.path:
                    raise ValueError("Provide either a token string or a token file path, not both.")
                if args.token:
                    token = deserialize(args.token)
                elif args.path:
                    with open(args.path, 'r') as file:
                        token = deserialize(file.read().strip())
                else:
                    raise ValueError("A token string or a token file path is required for 'validate' command.")
                print(auth_service.validate(token))

            case _:
                raise ValueError(f"Unsupported command '{args.command}'.")

    except RuntimeError as e:
        print(f"[{type(e).__name__}] {' '.join(e.args)}")
    except Exception as e:
        print(f"[{type(e).__name__}] {e}")
