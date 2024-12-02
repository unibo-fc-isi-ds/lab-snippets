from .example3_rpc_client import *
import argparse
import sys
import os



TOKEN_DIR  = os.getcwd()
TOKEN_DEFAULT_FILE = "token_file.json"

def write_token(token:Token, token_file = TOKEN_DEFAULT_FILE):
    file = open(token_file, "w")
    serialized_token = serialize(token)
    file.write(serialized_token)
    file.close()

def read_token(token_file = TOKEN_DEFAULT_FILE):
    file = open(token_file, "r")
    read_file = file.read()
    deserialized_token = deserialize(read_file)
    return deserialized_token


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
    parser.add_argument('--token_file_path', '-t', help='Token File Path')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    authentication_service = RemoteAuthDatabase(args.address)

    try :
        ids = (args.email or []) + [args.user]



        file_name = TOKEN_DEFAULT_FILE

        if args.token_file_path:
            file_name = args.token_file_path

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
                credentials = Credentials(ids[0], args.password)
                token = authentication_service.authenticate(credentials)
                write_token(token, file_name)
                print("Generated token:" + token.signature)
                print("Authentication successful")
            case 'validate':
                if not args.token_file_path:
                    print(Hello)
                    raise ValueError("Unspecified file")
                token = read_token(file_name)
                if authentication_service.validate_token(token):
                    print("Token with signature:" + token.signature + " is validated")
                else:
                    print("Token is not validated")
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
