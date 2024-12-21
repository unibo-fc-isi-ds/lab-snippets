from .example3_rpc_client import *
from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService

from datetime import timedelta, datetime

#from snippets.lab4.users import _compute_sha256_hash
import argparse
import sys


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check','authenticate','validate','auth-and-get'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    # for excercise 4-01
    parser.add_argument('--token','-t', help='Token String')
    parser.add_argument('--duration', '-d', help='Token duration in seconds', type=int)

    parser.add_argument('--token-file', help='Path to the token file')  # 添加 --token-file 参数


    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    auth_service = RemoteAuthenticationService(args.address)
    user_db = RemoteUserDatabase(args.address, auth_service)

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
                token = auth_service.get_saved_token()
                print('----------------token----------------')
                print(token)
                if token is None:
                    raise ValueError("You must authenticate before retrieving user data")
                user = user_db.get_user(ids[0])
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            
            case 'auth-and-get':
                # Authenticate and get user in one command
                if not args.password:
                    raise ValueError("Password is required")
                
                # Step 1: Authenticate and get token
                credentials = Credentials(ids[0], args.password)
                duration = timedelta(seconds=args.duration) if args.duration else timedelta(days=1)
                token = auth_service.authenticate(credentials, duration)
                
                auth_service.set_token(token)

                print('----------------saved token----------------')
                saved_token = auth_service.get_saved_token()
                print(saved_token)

                # Step 2: Immediately use the token to get user data
                print('----------------user data----------------')
                user_data = user_db.get_user(ids[0])
                print(user_data)
            # for excercise 4-01
            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                duration = timedelta(seconds=args.duration) if args.duration else timedelta(days=1)
                token = auth_service.authenticate(credentials, duration)  
                
                print('----------------token----------------')
                print(token)
                # 验证 token 是否被保存在 RemoteAuthenticationService
                saved_token = auth_service.get_saved_token()
                print('----------------saved token----------------')
                print(saved_token)
                user_db.set_token(saved_token)
            
            case 'validate':
                if not args.token:
                    raise ValueError("Token is required for validation")
                token = Token.deserialize(args.token)
                print(auth_service.validate_token(token))

            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
