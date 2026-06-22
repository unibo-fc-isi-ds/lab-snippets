from .example3_rpc_client import *
import argparse
import sys


if __name__ == '__main__':
    from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
    from snippets.lab4.example1_presentation import deserialize, serialize

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
    parser.add_argument('--token', '-t', help='Token (JSON string) for authorization')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    if args.token:
        try:
            user_db.token = deserialize(args.token)
        except Exception:
            print("Invalid token format provided")

    try :
        ids = (args.email or []) + ([args.user] if args.user else [])
        
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                if not args.user:
                    raise ValueError("Username is required")
                if not args.email:
                    raise ValueError("At least one email address is required")
                
                user = User(
                    username=args.user, 
                    emails=set(args.email), 
                    full_name=args.name, 
                    role=Role[args.role.upper()] if args.role else Role.USER, 
                    password=args.password
                )
                print(user_db.add_user(user))
            case 'get':
                if not ids:
                     raise ValueError("Username or email is required")
                print(user_db.get_user(ids[0]))
            case 'check':
                if not ids:
                     raise ValueError("Username or email is required")
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                if not ids:
                     raise ValueError("Username or email is required")
                credentials = Credentials(ids[0], args.password)
                token = auth_service.authenticate(credentials)
                print(serialize(token))
            case 'validate':
                 if not args.token:
                     raise ValueError("Token required for validation")
                 token_obj = deserialize(args.token)
                 print(auth_service.validate_token(token_obj))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
    except ValueError as e:
        print(f'[ValueError]', *e.args)