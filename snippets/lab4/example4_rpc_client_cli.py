from .example3_rpc_client import *
import argparse
import sys
from snippets.lab4.users.impl import save_token, load_token


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['user.add', 'user.get', 'user.check', 'auth.authenticate', 'auth.validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--duration', '-d', type=float, help='Duration of the token in seconds')
    parser.add_argument('--getUser', '-gU', help='The username of the user to get informations about')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    user_auth = RemoteUserAuthenticationService(args.address)

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        match args.command:
            case 'user.add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'user.get':
                if args.getUser:
                    print(user_db.get_user(args.getUser, token=load_token(ids[0])))
                else:    
                    print(user_db.get_user(ids[0], token=load_token(ids[0])))
            case 'user.check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'auth.authenticate':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                duration = timedelta(seconds=float(args.duration)) if args.duration else None
                token = user_auth.authenticate(credentials, duration)
                save_token(token)
                print(token)
            case 'auth.validate':
                if user_auth.token is None:
                    raise ValueError("No token available, authenticate first.")
                user_auth.validate_token(user_auth.token)
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
