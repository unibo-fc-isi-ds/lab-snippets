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
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'auth', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--duration', '-d', type=float, help='Duration in seconds')
    parser.add_argument('--token', '-t', help='Token (JSON)')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    if args.token:
        user_db.token = deserialize(args.token)

    try :
        ids = (args.email or []) + ([args.user] if args.user else [])
        match args.command:
            case 'add':
                if len(ids) == 0:
                    raise ValueError("Username or email address is required")
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()] if args.role else Role.USER, args.password)
                print(user_db.add_user(user))
            case 'get':
                if len(ids) == 0:
                    raise ValueError("Username or email address is required")
                print(user_db.get_user(ids[0]))
            case 'check':
                if len(ids) == 0:
                    raise ValueError("Username or email address is required")
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'auth':
                if len(ids) == 0:
                    raise ValueError("Username or email address is required")
                credentials = Credentials(ids[0], args.password)
                duration = timedelta(seconds=args.duration) if args.duration else None
                print(serialize(auth_service.authenticate(credentials, duration)))
            case 'validate':
                if not args.token:
                    raise ValueError("Token is required")
                token = deserialize(args.token)
                print(auth_service.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
