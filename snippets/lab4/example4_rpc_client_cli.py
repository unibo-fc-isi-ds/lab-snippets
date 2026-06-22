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

def first_user(u):
    return u[0] if isinstance(u, list) else u
# This function is used because now -u argument is a list but for mathods which re not
# check or get, we have to have just one username.

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
    parser.add_argument('--user', '-u', action='append', help='Username(s)')
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
        if not args.user:
            raise ValueError("You must specify at least one -u")
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                username = first_user(args.user)
                user = User(username, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get': # Now protected
                if not args.user:
                    raise ValueError("You must specify who re u and who do u want to read")
                requester = args.user[0]
                target = args.user[-1]
                token = load_token(requester)
                print(user_db.get_user(target, token=token))
            case 'check': # Now protected
                if not args.user:
                    raise ValueError("You must specify who re u and who do u want to check")
                requester = args.user[0]
                target = args.user[-1]
                print("DEBUG requester:", requester, type(requester))
                print("DEBUG target:", target, type(target))
                token = load_token(requester)
                if not args.password:
                    raise ValueError("Password is required for check")
                credentials = Credentials(target, args.password)
                print(user_db.check_password(credentials, token=token))
            case 'auth':
                username = first_user(args.user)
                credentials = Credentials(username, args.password)
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
                username = first_user(args.user)
                token = load_token(username)
                if auth.validate_token(token):
                    print("U re user:", token.user)
                else:
                    print("Invalid or expired token!")
            case 'logout':
                if not args.user:
                    raise ValueError("Username is required for logout")
                username = first_user(args.user)
                logout_user(username)
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
