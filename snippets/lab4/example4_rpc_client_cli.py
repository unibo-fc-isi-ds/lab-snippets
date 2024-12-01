from .example3_rpc_client import *
import argparse
import sys
from snippets.lab4.example1_presentation import serialize, deserialize

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
    parser.add_argument('--token', '-t', help='Token')
    parser.add_argument('--expiration', '-e', help='Token expiration')
    parser.add_argument('--no-save', '-ns', help='Do not save token')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0 and args.command != 'validate':
            raise ValueError("Username or email address is required")
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'auth':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(args.user, args.password)
                print(user_db.authenticate(credentials))
                if not args.no_save:
                    try:
                        with open('token.txt', 'w') as f:
                            f.write(serialize(user_db.token))
                        print(f"Token saved: {user_db.token}")
                    except Exception as e:
                        print(f"Error saving token: {e}")
            case 'validate':
                try:
                    with open('token.txt', 'r') as f:
                        token = deserialize(f.read())
                except Exception as e:
                    print(f"Error reading token: {e}")
                    
                print(user_db.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
