from .example3_rpc_client import *
import argparse
import sys
from datetime import timedelta # For manage token duration
import os

def save_token(token):
    filename = f".token_{token.user.username}"
    with open(filename, "w") as f:
        f.write(serialize(token))
    print(f"Token saved in {filename}")

def load_token(username):
    filename = f".token_{username}"
    if not os.path.exists(filename):
        raise RuntimeError(f"No token found for user {username}. Please authenticate first.")
    with open(filename, "r") as f:
        return deserialize(f.read())
    
def logout_user(username):
    filename = f".token_{username}"
    if os.path.exists(filename):
        os.remove(filename)
        print(f"Logged out {username}. Token file {filename} deleted.")
    else:
        print(f"No token found for user {username}.")
# This functions re used for the "whoami" method, with this functions there is no more need
# to write the token by hand.
# Now we just need whoami -u "username", for each autenticated users a new .token file will be created.
# The function logout is used to delete the .token_"username" file 



if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'auth', 'whoami', 'logout'])
    # New methods auth for authentication and whoami method which require token validation
    # logout for deleting user .token's file
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--duration', '-d', type=int,
                        help='Token duration in seconds (default: 24h)')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth = RemoteAuthenticationService(args.address)

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
            case 'auth':
                credentials = Credentials(ids[0], args.password)
                # Manage the case -d in interface or not (standard of the server in that case 1 day)
                duration = None
                if args.duration is not None:
                    duration = timedelta(seconds=args.duration)
                token = auth.authenticate(credentials, duration)
                print("Authentication successfully!")
                print("User:", token.user)
                print("The token generated expires at:", token.expiration)
                save_token(token)
            case 'whoami':
                token = load_token(args.user)
                if auth.validate_token(token):
                    print("U re user:", token.user)
                else:
                    print("Invalid or expired token!")
            case 'logout':
                if not args.user:
                    raise ValueError("Username is required for logout")
                logout_user(args.user)
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
