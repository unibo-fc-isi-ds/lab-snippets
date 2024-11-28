from .example3_rpc_client import *
import argparse
import shlex
import sys

def execute(args, user_db: RemoteUserDatabase, user_auth: RemoteUserAuthentication):
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
                print(user_db.get_user(ids[0], user_auth.token))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'auth':
                credentials = Credentials(ids[0], args.password)
                print(user_auth.authenticate(credentials))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)

if __name__ == '__main__':
    
    args = None
    user_db = None
    user_auth = None

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    
    parser.add_argument('address', help='Server address in the form ip:port')
    
    if (len(sys.argv) > 1):
        args = parser.parse_args(sys.argv[1:])
        user_db = RemoteUserDatabase(address(args.address))
        user_auth = RemoteUserAuthentication(address(args.address))
    else:
        parser.print_help()
        sys.exit(1)
        
    parser = argparse.ArgumentParser(
        description='RPC client for user database',
        exit_on_error=False,
    )
    
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'auth'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')

    parser.print_help()

    while True:
        try:
            print()
            user_input = input('Enter command: ')
            if user_input.strip():
                args = parser.parse_args(shlex.split(user_input))
                execute(args, user_db, user_auth)
            else:
                parser.print_help()
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)
