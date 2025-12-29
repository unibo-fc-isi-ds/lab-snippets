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
    parser.add_argument('command', help='Method to call', choices=['authenticate', 'add', 'get', 'check'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token', '-t', help='Authentication token signature') #Since there is no way to pass a whole Token object as a CLI input, only its signature needs to be passed. This is only for the sake of this exercise: in real projects, JWT tokens would be used

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db_with_authentication = RemoteDatabaseServiceWithAuthentication(address(sys.argv[1]))

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        match args.command:
            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.user:
                    raise ValueError("Username is required")
                print(user_db_with_authentication.authenticate(Credentials(ids[0], args.password)).signature)
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db_with_authentication.add_user(user))
            case 'get':
                if not args.token:
                    raise ValueError("Authentication token is required")
                print("Token: ", args.token)
                print("User ID: ", ids[0])
                signature = args.token
                print(user_db_with_authentication.get_user(ids[0], token=None, tokenSignature=signature))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db_with_authentication.check_password(credentials))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
