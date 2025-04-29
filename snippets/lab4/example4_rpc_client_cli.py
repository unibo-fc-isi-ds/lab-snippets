import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from snippets.lab4.example3_rpc_client import *
import argparse
import sys


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check','auth','validate'])
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
                user = User(
                    username=args.user,
                    emails=set(args.email),  # Convert list to set
                    full_name=args.name,
                    role=Role[args.role.upper()],  # Convert role to enum
                    password=args.password
                )
                print(user_db.add_user(user))
            case 'get':
                if not auth_service.token:
                    print("Authentication required. Use the 'auth' command first.")
                    sys.exit(1)
                print(user_db.get_user(args.user))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'auth' :
                credentials = Credentials(args.user, args.password)
                token = auth_service.authenticate(credentials)
                print(f"Authenticated. Token: {token}")
                auth_service.token = serialize(token)  # Save the token
            case 'validate' :
                serialized_token = input("Enter serialized token: ")
                auth_token = deserialize(serialized_token)
                print(f"Deserialized token: {auth_token}")  # Debugging line
                if not isinstance(auth_token, Token):
                    raise ValueError(f"Deserialization failed: Expected Token, got {type(auth_token)}")
                auth_service = RemoteAuthenticationService(args.address)
                print(auth_service.validate_token(auth_token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
            
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
