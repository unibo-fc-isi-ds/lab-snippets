from .example3_rpc_client import *
import argparse
import sys
from snippets.lab4.example1_presentation import serialize, deserialize, TokenHandler, TOKENS_FOLDER

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
    parser.add_argument('--token-user', '-t', help='Token user')
    parser.add_argument('--token-path', '-tp', help=f'Path to token (defaults to {TOKENS_FOLDER})')
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
        if len(ids) == 0:
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
                if not args.token_user:
                    print('Username is required for this action')
                token = TokenHandler.load_user_token(args.token_user)
                if not token:
                    print(f"Token for user {args.token_user} not found")
                print(user_db.get_user(ids[0], token))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'auth':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                token = user_db.authenticate(credentials)
                print(token)
                if not args.no_save:
                    TokenHandler.store(token)
            case 'validate':
                if not args.token_user and not args.token_path:
                    raise ValueError("Username or token path are required for this action")
                try:
                    if not args.token_path:
                        token = TokenHandler.load_user_token(args.token_user)
                    else:
                        token = TokenHandler.load(args.token_path)
                    print(user_db.validate_token(token))
                except Exception as e:
                    print(f'[{type(e).__name__}]', *e.args)
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
