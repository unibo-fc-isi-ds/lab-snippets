from .example3_rpc_client import *
import argparse
import os
import sys


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate', 'validate', 'delete_token'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token', '-t', help='Token Path')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    
    token_path = args.token or './token.json'
        
    try:
        with open(token_path) as f:
            token = deserialize(f.read())
            if not isinstance(token, Token):
                print("Token is corrupted")
                token = None
    except FileNotFoundError:
        token = None
        print("Token file not provided\n")
    
    user_db = RemoteUserDatabase(args.address, token)
    user_auth = RemoteAuthenticationService(args.address, token)

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
                response = user_db.add_user(user)
                print("User added successfully" if response is None else response)
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                credentials = Credentials(ids[0], args.password)
                response = user_auth.authenticate(credentials)
                print(response)
                if response is not None:
                    user_db.store_token(response) # When authenticated the new token is stored and will be used for further requests
                    user_auth.store_token(response)
                    with open(token_path, 'w') as f:
                        f.write(serialize(response)) # Save the token to a file, overwriting the previous one if present
                        print(f'Token saved to {token_path}')
            case 'validate':
                print("Given token is valid" if user_auth.validate_token(token) else "Given token is invalid")
            case 'delete_token':
                if os.path.exists(token_path):
                    os.remove(token_path)
                else:
                    print("Error: couldn't find the token file")
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
