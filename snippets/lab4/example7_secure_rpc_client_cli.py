from snippets.lab4.example6_secure_rpc_client import SecureRemoteAuthenticationDatabaseService
from .example3_rpc_client import *
import argparse
import sys


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 7',
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
    parser.add_argument('--duration', '-d', help='Token duration in seconds', type=int)
    parser.add_argument('--datetime', '-dt', help='Datetime in the format YYYY-MM-DDTHH:MM:SS')
    parser.add_argument('--signature', '-s', help='Token signature')
    parser.add_argument('--admin_user', '-au', help='Username of admin')
    parser.add_argument('--admin_email', '--aaddress', '-aa', nargs='+', help='Email address of admin')
    parser.add_argument('--admin_name', '-an', help='Full name of admin')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    db_auth_service = SecureRemoteAuthenticationDatabaseService(address(sys.argv[1]))

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
                print(db_auth_service.add_user(user))
            case 'get':
                if not args.admin_user or not args.admin_email or not args.admin_name or not args.role or not args.datetime or not args.signature:
                    raise ValueError("The following admin information is needed to create a Token: Username, Email, Full Name, Role, Datetime and Signature")
                admin_token = Token(User(args.admin_user, args.admin_email, args.admin_name, Role[args.role.upper()]), datetime.fromisoformat(args.datetime), args.signature)
                print(db_auth_service.get_user(ids[0], metadata=admin_token))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(db_auth_service.check_password(credentials))
            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                duration = timedelta(seconds=args.duration) if args.duration else None
                print(db_auth_service.authenticate(credentials, duration))
            case 'validate':
                if not args.user or not args.email or not args.name or not args.role or not args.datetime or not args.signature:
                    raise ValueError("Username, Email, Full Name, Role, Datetime and Signature are required to create a token")
                token = Token(User(args.user, args.email, args.name, Role[args.role.upper()]), datetime.fromisoformat(args.datetime), args.signature)
                print(db_auth_service.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
