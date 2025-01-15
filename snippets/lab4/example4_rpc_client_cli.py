from snippets.lab4.example0_users import _PRINT_LOGS
from snippets.lab4.users.impl import InMemoryUserDatabase
from .example3_rpc_client import *
import argparse
import sys


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
    parser.add_argument('--token', '-t', help='Token as string')
    parser.add_argument('--path', '-th', help='File path for token storage or retrieval')

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

        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()] if args.role else Role.USER, args.password)
                print(user_db.add_user(user))

            case 'get':
                if args.path:
                    with open(args.path, 'r') as file:
                        token = file.read().strip()
                elif args.token:
                    token = args.token
                else:
                    raise ValueError("A token (or its file path) is required")
                print(user_db.get_user(ids[0], deserialize(token)))

            case 'check':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))

            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                token = auth_service.authenticate(credentials)
                print(f"User '{args.user}' authenticated successfully")
                if args.path:
                    with open(args.path, 'w') as f:
                        f.write(serialize(token))
                print(token)

            case 'validate':
                if args.token and args.path:
                    raise ValueError("Provide either a token or a file path, not both")
                if args.token:
                    token = args.token
                elif args.path:
                    with open(args.path, 'r') as file:
                        token = file.read().strip()
                else:
                    raise ValueError("A token (or its file path) is required")
                print(auth_service.validate(deserialize(token)))

            case _:
                raise ValueError(f"Invalid command '{args.command}'")

    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
