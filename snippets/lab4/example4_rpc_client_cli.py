from .example3_rpc_client import *
from .example1_presentation import Serializer, Deserializer
import argparse
import sys
import os

TOKENS_DIR = './snippets/lab4/tokens'

def get_token_file(username: str) -> str:
    return f'{TOKENS_DIR}/{username}.json'

def save_token_to_file(file_name: str, token: Token) -> None:
    if not os.path.exists(TOKENS_DIR):
        os.makedirs(TOKENS_DIR)
    file_path = get_token_file(file_name)
    with open(file_path, 'w') as f:
        serializer = Serializer()
        f.write(serializer.serialize(token))

def read_token_from_file(file_name: str) -> Token:
    file_path = get_token_file(file_name)
    with open(file_path, 'r') as f:
        deserializer = Deserializer()
        return deserializer.deserialize(f.read())

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate', 'validate_token'])
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
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required")
                
                credentials = Credentials(ids[0], args.password)
                token = auth_service.authenticate(credentials)
                print(token)
                save_token_to_file(file_name=token.user.username, token=token)
            case 'validate_token':
                if not args.user:
                    raise ValueError("Username is required")
                token = read_token_from_file(args.user)
                print("Token is valid" if auth_service.validate_token(token) 
                                       else "Token expired")
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
