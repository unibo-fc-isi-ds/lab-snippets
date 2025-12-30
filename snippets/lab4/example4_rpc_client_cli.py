from .example3_rpc_client import *
from snippets.lab4.example1_presentation import serialize, deserialize
import argparse
import sys
import os

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate', 'validateToken'])
    parser.add_argument('--user', '-u', help='Username')                                     # Always require username in CLI commands
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--duration', '-d', type=float, help='Requested duration (in days)')                # Token duration in DAYS

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    token_dir = "./snippets/lab4/tokens"            # Token saving path
    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        
        current_user_id = ids[0]
        token_path = os.path.join(token_dir, f"{current_user_id}.token")

        # If the token of the current user exists, it il loaded in the ClientStub
        if os.path.exists(token_path):
            try:
                with open(token_path, 'r') as f:
                    saved_token = deserialize(f.read())
                    # Injection in stubs
                    user_db.token = saved_token
                    auth_service.token = saved_token
                    print(f"# Active session loaded for user: {current_user_id}")
            except Exception as e:
                print(f"Warning: Could not load existing token for {current_user_id}: {e}")

        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))

            case 'get':
                print(user_db.get_user(current_user_id))

            case 'check':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(current_user_id, args.password)
                print(user_db.check_password(credentials))

            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required")                
                credentials = Credentials(current_user_id, args.password)
                
                duration = timedelta(days=args.duration) if args.duration else None
                token = auth_service.authenticate(credentials, duration)

                # Saves token for current user
                if not os.path.exists(token_dir):
                    os.makedirs(token_dir)
                with open(token_path, 'w') as f:
                    f.write(serialize(token))

                print(f"Authentication successful! Token for '{current_user_id}' saved to {token_path}")

            case 'validateToken':
                if not os.path.exists(token_path):
                    raise FileNotFoundError(f"No local token file found for user: {current_user_id}")
                
                with open(token_path, 'r') as f:
                    token = deserialize(f.read())
                
                is_valid = auth_service.validate_token(token)
                status = "VALID" if is_valid else "INVALID or EXPIRED"
                print(f"Token status for '{current_user_id}': {status}")

            case _:
                raise ValueError(f"Invalid command '{args.command}'")
            
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
