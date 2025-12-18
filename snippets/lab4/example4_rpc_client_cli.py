from .example3_rpc_client import *
import argparse
import sys
from datetime import timedelta
import json
import os

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check','authenticate' ,'validate' ])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--duration', '-d', help='Authentication token duration')
    parser.add_argument('--token', '-t', help='Authentication token')
    
    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthService(args.address)
    
    try :
        ids = (args.email or []) + ([args.user] if args.user else [])
        main_id = ids[0] if ids else None
        
        match args.command:
            case 'add':
                if not args.user and not args.email:
                    raise ValueError("Username or email address is required")
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get': 
                if not main_id:
                    raise ValueError("Username or email address is required")
                
                json_string = None
                if args.token:
                    json_string = args.token
                if not json_string and os.path.exists(".token.json"):
                    with open(".token.json", "r") as f:
                        json_string = f.read()
                elif not sys.stdin.isatty():
                    full_input = sys.stdin.read()
                    
                    filtered_lines = []
                    for line in full_input.splitlines():
                        if not line.strip().startswith('#') and line.strip(): 
                            filtered_lines.append(line)
                    
                    json_string = '\n'.join(filtered_lines).strip()
                
                if json_string:
                    try:
                        token_obj = deserialize(json_string) 
                        token_dict_data = json.loads(serialize(token_obj))
                        user_db.set_auth_token(token_dict_data)
                    except Exception as e:
                        raise ValueError(f"Invalid token format provided to 'get': {e}")
                print(user_db.get_user(main_id))
            case 'check':
                if not main_id or not args.password:
                    raise ValueError("Username/email and password are required")
                credentials = Credentials(main_id, args.password)
                print(user_db.check_password(credentials))
            case 'authenticate': 
                if not main_id or not args.password:
                    raise ValueError("Username/email and password are required")
                credentials = Credentials(main_id, args.password)
                if not args.duration:
                    duration = None
                else:
                    duration = timedelta(seconds=int(args.duration))
                token = auth_service.authenticate(credentials, duration)
                token_json = serialize(token)
                with open(".token.json", "w") as f:
                    f.write(token_json)
                print(serialize(token_json))
                import json
                token_dict_data = json.loads(serialize(token)) 
                
                user_db.set_auth_token(token_dict_data)
                print(serialize(token))
            case 'validate':
                json_string = None
                if args.token:
                    json_string = args.token
                else:
                    import sys
                    json_string = sys.stdin.read().strip()
                if not json_string:
                    raise ValueError ("Token required use pipe JSON")
                token_obj = deserialize(json_string)
                is_valid = auth_service.validate_token(token_obj)
                print("Valid token" if is_valid else "token not valid")
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
