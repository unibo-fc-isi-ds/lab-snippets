from .example3_rpc_client import *
import argparse
import sys
import json
import os



current_dir = os.path.dirname(os.path.abspath(__file__))
subdir = os.path.join(current_dir, "tmp")
os.makedirs(subdir, exist_ok=True)
TOKEN_FILE = os.path.join(subdir, "tokens.json")



def save_token(username, token):
    try:
        if os.path.exists(TOKEN_FILE):
            with open(TOKEN_FILE, "r") as f:
                tokens = json.load(f)
        else:
            tokens = {}
        tokens[username] = {
            "expiration": token.expiration.isoformat(),
            "signature": token.signature,
        }
        with open(TOKEN_FILE, "w") as f:
            json.dump(tokens, f, indent=4)
    except Exception as e:
        print(f"Error saving token: {e}")

def load_token(username):
    if not os.path.exists(TOKEN_FILE):
        raise ValueError("No token file found")
    with open(TOKEN_FILE, "r") as f:
        tokens = json.load(f)
    if username not in tokens:
        raise ValueError(f"No token found for user '{username}'")
    data = tokens[username]
    expiration = datetime.fromisoformat(data["expiration"])
    signature = data["signature"]
    return expiration, signature



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
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required for authentication")
                credentials = Credentials(ids[0], args.password)
                token = auth_service.authenticate(credentials)
                print("Token generated:", token)
                save_token(ids[0], token)
            case 'validate':
                expiration, signature = load_token(ids[0])
                user = user_db.get_user(ids[0])
                token = Token(user=user, expiration=expiration, signature=signature)
                print(auth_service.validate(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
