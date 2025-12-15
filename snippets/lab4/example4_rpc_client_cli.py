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
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'login', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')

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
                role_name = args.role.upper() if args.role else 'USER'
                role_enum = Role[role_name]
                user = User(args.user, args.email, args.name, role_enum, args.password)
                print(user_db.add_user(user))
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'login':
                if not args.user and not args.email:
                    raise ValueError("Username or email address is required")
                if not args.password:
                    raise ValueError("Password is required")
                login_id = args.user if args.user else args.email[0]
                creds = Credentials(login_id, args.password)
                token = auth_service.authenticate(creds)
                print("Token:", token)
                print("Signature:", token.signature)
            case 'validate':
                if not args.user and not args.email:
                    raise ValueError("Username or email is required")
                if not args.password:
                    raise ValueError("Password is required")
                login_id = args.user if args.user else args.email[0]
                creds = Credentials(login_id, args.password)
                token = auth_service.authenticate(creds)
                is_valid = auth_service.validate_token(token)
                if is_valid:
                    print("Token validated.")
                else:
                    print("Token invalid.")
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
    except Exception as e:
        print(f'Error: ', e)
