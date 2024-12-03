from snippets.lab4.example3_rpc_client import RemoteUserAuth
from snippets.lab4.tokens import TokenStorage
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
    parser.add_argument('--auth-user', '-au', help='Username for authentication')
    parser.add_argument('--auth-password', '-ap', help='Password for authentication')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    user_auth = RemoteUserAuth(args.address)    

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        match args.command:
            case 'add': # Add user
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_auth.add_user(user))
            case 'get': # Get a user (requires authentication and authorization)
                credentials = Credentials(args.auth_user, args.auth_password)
                token = TokenStorage().load(credentials.id)
                user_auth.check_privileges(user_db, credentials, token)
                print(user_auth.get_user(ids[0], metadata=token))
            case 'check': # Check password
                credentials = Credentials(ids[0], args.password)
                print(user_auth.check_password(credentials))
            case 'auth': # Authenticate
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(args.user, args.password)
                token = user_auth.authenticate(credentials)
                TokenStorage().save(token)
                print(token)
            case 'validate': # Validate token
                if not args.user:
                    raise ValueError("Username is required")
                token = TokenStorage().load(args.user)
                if user_auth.validate_token(token):
                    print('Token is valid')
                else:
                    print('Token is invalid')
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)