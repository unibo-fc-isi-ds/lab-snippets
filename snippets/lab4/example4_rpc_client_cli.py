import os
from .example3_rpc_client import *
import argparse
import sys


def read_file(file):
    file_path = f"{file}.txt"
    if not os.path.exists(file_path):
        return False
    with open(file_path, "r") as f:
        return f.read()

def write_file(file, content):
    with open(f"{file}.txt", "w") as f:
        f.write(content)
       


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate','validate'])
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
    user_auth = RemoteUserAuth(args.address)

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
            case "get":
                user_requester = input("Enter your username or email address: ")
                password_requester = input("Enter your password: ")
                
                if not user_db.check_password(Credentials(user_requester, password_requester)):
                    raise ValueError("Invalid username or password")
                
                token_requester = read_file(user_requester)
                if not token_requester:
                    raise ValueError("Authentication required")
                
                token_requester = deserialize(token_requester)
                if not (token_requester.user.role == Role.ADMIN and user_auth.validate_token(token_requester)):
                    raise ValueError("Unauthorized access to user")
                
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case "authenticate":
                credentials = Credentials(ids[0], args.password)
                result = user_auth.authenticate(credentials)
                write_file(ids[0], serialize(result))
                print(result)

            case "validate":
                if not args.password or not args.user:
                    raise ValueError("Password and Username are required")
                token_content = deserialize(read_file(ids[0]))
                print(user_auth.validate_token(token_content))

            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)