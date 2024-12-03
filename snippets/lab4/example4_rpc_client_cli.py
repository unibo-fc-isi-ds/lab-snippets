from .example3_rpc_client import *
import argparse
import sys


def __check_password_provided(args):
    if not args.password:
        raise ValueError("Password is required")

def __strip_token(args):
    with open(args.path, 'r') as file:
        token = file.read().strip()
        return token

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
    parser.add_argument('--token', '-t', help='Token')
    parser.add_argument('--path', '-th', help='Token path')

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
                __check_password_provided(args)
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                if not args.token and not args.path:
                    raise ValueError("Token is required, only admins can perform this operation")
                elif args.token:
                    print(user_db.get_user(ids[0], deserialize(args.token)))
                elif args.path:
                    token = __strip_token(args)
                    print(user_db.get_user(ids[0], deserialize(token)))
                else:
                    raise ValueError("Something went wrong, check your inputs")
                
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))

            case 'authenticate':
                credentials = Credentials(ids[0], args.password)
                __check_password_provided(args)
                token = auth.authenticate(credentials)
                print("User logged in")
                if args.path:
                    with open(args.path, 'w') as f:
                        f.write(serialize(token))
                print(token)

            case 'validate':
                if args.token:
                    token = args.token
                elif args.path:
                    token = __strip_token(args)
                elif args.token and args.path:
                    token = args.token
                else:
                    raise ValueError("Provide a token or a path to a token file")
                print(auth.validate(deserialize(token)))
                
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
