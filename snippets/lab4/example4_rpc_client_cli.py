from snippets.lab4.example3_rpc_client import RemoteAuthenticathion
from snippets.lab4.tokenHandler import TokenHandler
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
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check','auth','validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--authentication-user', '-au', help='Username for authentication')
    parser.add_argument('--authentication-password', '-ap', help='Password for authentication')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    user_authentication= RemoteAuthenticathion(args.address)

    try:
        ids = (args.email or []) + [args.user]
        if not ids:
            raise ValueError("Username or email address is required.")

        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required.")
                if not args.name:
                    raise ValueError("Full name is required.")

                user = User(
                    username=args.user,
                    email=args.email,
                    full_name=args.name,
                    role=Role[args.role.upper()],
                    password=args.password
                )
                result = user_authentication.add_user(user)
                print(f"User added successfully: {result}")

            case 'get':
                credentials = Credentials(args.authentication_user, args.authentication_password)
                token = TokenHandler().load_token(credentials.id)
                user_authentication.check_user_privileges(user_db, credentials, token)
                user = user_authentication.get_user(ids[0], metadata=token)
                print(f"User data: {user}")

            case 'check':
                credentials = Credentials(ids[0], args.password)
                is_valid = user_authentication.check_password(credentials)
                print(f"Password validation result: {is_valid}")

            case 'auth':
                if not args.password:
                    raise ValueError("Password is required for authentication.")
                
                credentials = Credentials(ids[0], args.password)
                token = user_authentication.authenticate(credentials)
                TokenHandler().save_token(token)
                print(f"Authentication successful. Token saved for user: {credentials.id}")

            case 'validate':
                token = TokenHandler().load_token(args.user)
                user = user_authentication.validate_token(token)
                print(f"Token is valid for user: {user}")

            case _:
                raise ValueError(f"Invalid command '{args.command}'")

    except ValueError as e:
        print(f"[ValueError] {e}")

    except RuntimeError as e:
        print(f"[RuntimeError] {e}")

    except Exception as e:
        print(f"[{type(e).__name__}] An unexpected error occurred: {e}")

