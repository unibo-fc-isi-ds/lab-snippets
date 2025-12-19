from .example3_rpc_client import *
import argparse
import sys
from datetime import timedelta


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'login', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--duration', '-d', type=int, help='Token duration in seconds (only for login)')
    parser.add_argument('--token', '-t', help='Serialized token (JSON) to validate')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    try:
        if args.command == 'add':
            if not args.user:
                raise ValueError("--user is required")
            if not args.password:
                raise ValueError("Password is required")
            if not args.name:
                raise ValueError("Full name is required")

            user = User(
                args.user,
                args.email,
                args.name,
                Role[args.role.upper()],
                args.password
            )
            print(user_db.add_user(user))

        elif args.command == 'get':
            ids = (args.email or []) + [args.user]
            ids = [i for i in ids if i]
            if len(ids) == 0:
                raise ValueError("Username or email address is required")

            print(user_db.get_user(ids[0]))
    
        elif args.command == 'check':
            ids = (args.email or []) + [args.user]
            ids = [i for i in ids if i]
            if len(ids) == 0:
                raise ValueError("Username or email address is required")
            if not args.password:
                raise ValueError("Password is required")

            credentials = Credentials(ids[0], args.password)
            print(user_db.check_password(credentials))
    
        elif args.command == 'login':
            ids = (args.email or []) + [args.user]
            ids = [i for i in ids if i]
            if len(ids) == 0:
                raise ValueError("Username or email address is required")
            if not args.password:
                raise ValueError("Password is required")

            credentials = Credentials(ids[0], args.password)
            duration = timedelta(seconds=args.duration) if args.duration is not None else None
            token = auth_service.authenticate(credentials, duration)

            # Print the token both as an object and as a serialized JSON that can be reused with --token
            print(token)
            print('# Copy/paste this for validation with --token')
            print(serialize(token))
    
        elif args.command == 'validate':
            if not args.token:
                raise ValueError("--token is required for validate")

            token = deserialize(args.token)
            if not isinstance(token, Token):
                raise ValueError("--token must be a serialized Token")

            print(auth_service.validate_token(token))
        else:
            raise ValueError(f"Invalid command '{args.command}'")

    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)


    
