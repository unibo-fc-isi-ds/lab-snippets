from .example3_rpc_client import *
import argparse
import sys
from .users.impl import *
import os
from .example1_presentation import *

def read_token_from_file(username):
    try:
        with open(f"{username}.txt", 'rt') as f:
            data = f.read()
            ast = Deserializer()._string_to_ast(data)
            return Deserializer()._ast_to_token(ast)
    except FileNotFoundError:
        raise ValueError(f"Token file for '{username}' not found")

def write_token_to_file(username, token):
    with open(f"{username}.txt", 'w') as f:
        f.write(serialize(token))

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authentication', 'validate_token'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--target', '-p', help='TargetUser')

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
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                token = read_token_from_file(args.user)
                print(user_db.get_user(args.target, token))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authentication': 
                if not args.user:
                    raise ValueError("Username is required")
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(args.user, args.password)
                token = auth_service.authenticate(credentials)
                if isinstance(token, Token):
                    write_token_to_file(args.user, token)
                print(token)
            case 'validate_token': 
                if not args.user:
                    raise ValueError("Username is required")
                token = read_token_from_file(args.user)
                print(auth_service.validate_token(token))                        
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
