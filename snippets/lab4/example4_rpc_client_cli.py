from .example3_rpc_client import *
import argparse
import sys
from datetime import timedelta
import os


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
    parser.add_argument('--tokenpath', '-t', help='The path from home directory where the token will be saved')
    parser.add_argument('--tokenduration', '-d', help='The duration of the token expressed in hours (floating value is accepted)')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

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
                if not args.role:
                    user = User(args.user, args.email, args.name, password=args.password)
                else:
                    user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                if not ids[0]:
                    raise ValueError("Username or email is required")
                default_path = os.path.join(os.path.expanduser('~'), f'{ids[0]}.json')
                path = default_path if not args.tokenpath else os.path.join(os.path.expanduser('~'), args.tokenpath)
                print(path)
                token = auth_service.get_token_from_file(ids[0], path)
                print(user_db.get_user(ids[0], token))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                credentials = Credentials(ids[0], args.password)
                if args.tokenduration:
                    duration = timedelta(hours=float(args.tokenduration))
                    token = auth_service.authenticate(credentials, duration)
                else:
                    token = auth_service.authenticate(credentials)
                print(token) # print the token
                # save the token in a json file
                default_path = os.path.join(os.path.expanduser('~'), f'{ids[0]}.json')
                path = default_path if not args.tokenpath else os.path.join(os.path.expanduser('~'), args.tokenpath)
                auth_service.save_token_to_file(token, path)
            case 'validate':
                if not (args.user or args.tokenpath):
                    raise ValueError("One of username and token path is required")
                default_path = os.path.join(os.path.expanduser('~'), f'{args.user}.json')
                path = default_path if not args.tokenpath else os.path.join(os.path.expanduser('~'), args.tokenpath)
                token = auth_service.get_token_from_file(args.user, path)
                print(auth_service.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
