# client.py
from .example3_rpc_client import *
import argparse
import sys


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client supporting user database + authentication service',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument(
        'command',
        help='Method to call',
        choices=['add', 'get', 'check', 'auth', 'validate']
    )
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a',
                        nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument(
        '--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p',
                        help='Password or token-serialized')
    parser.add_argument('--token', '-t', help='Serialized token value')
    parser.add_argument('--duration', '-d', type=int,
                        help='Token duration in seconds')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)

    user_db = RemoteUserDatabase(args.address)
    auth = RemoteAuthenticationService(args.address)

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
                emails = args.email if args.email is not None else []
                role_str = args.role.upper() if args.role else "USER"
                user = User(args.user, emails, args.name,
                            Role[role_str], args.password)
                print(user_db.add_user(user))

            case 'get':
                if not args.token:
                    raise ValueError("get_user requires --token for authorization")
                token = deserialize(args.token)
                print(user_db.get_user(ids[0], token))

            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))

            case 'auth':
                if args.duration is not None:
                    duration = args.duration
                else:
                    duration = 3600  # default 1 hour in seconds
                credentials = Credentials(args.user, args.password)
                token = auth.authenticate(credentials, duration)
                print(token)

            case 'validate':
                if not args.token:
                    raise ValueError(
                        "You must pass --token containing a serialized token")
                token = deserialize(args.token)
                print(auth.validate_token(token))

            case _:
                raise ValueError(f"Invalid command '{args.command}'")

    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
