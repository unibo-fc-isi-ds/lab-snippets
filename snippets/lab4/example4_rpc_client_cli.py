from .example3_rpc_client import *
import argparse
import sys
from pathlib import Path


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'get_token', 'val_token'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token-file', '-tf', help='Path to a file containing the serialized Token JSON')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    # Token cache file
    TOKEN_CACHE_FILE = Path('token_cached.json')
    
    # Auto-load cached token if it exists
    if TOKEN_CACHE_FILE.exists():
        from snippets.lab4.example1_presentation import deserialize
        try:
            with open(TOKEN_CACHE_FILE, 'r', encoding='utf-8') as f:
                token_str = f.read()
            cached_token = deserialize(token_str)
            user_db.set_token(cached_token)
            print(f"# Loaded cached token from {TOKEN_CACHE_FILE}")
        except Exception as e:
            print(f"# Warning: Could not load cached token: {e}")

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0 and args.command not in ['val_token']:
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
            case 'get_token':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                token = auth_service.authenticate(credentials)
                print(serialize(token))
            case 'val_token':
                from snippets.lab4.example1_presentation import deserialize
                if not args.token_file:
                    raise ValueError("Token file is required: use --token-file <path>")
                with open(args.token_file, 'r', encoding='utf-8') as f:
                    token_str = f.read()
                token = deserialize(token_str)
                is_token_valid = auth_service.validate_token(token)
                print(is_token_valid)
                if is_token_valid:
                    # Store token in client stub and cache to file
                    user_db.set_token(token)
                    with open(TOKEN_CACHE_FILE, 'w', encoding='utf-8') as f:
                        f.write(serialize(token))
                    print(f"# Token cached to {TOKEN_CACHE_FILE}")
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
