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
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check','auth', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--tokenPath', '-tP', help='tokenPath')
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
    auth_srvc = RemoteAuthService(args.address)
    token:Token = None

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
            case 'auth':
                file = args.tokenPath
                if not args.tokenPath:
                    file = "token.txt"
                credentials = Credentials(ids[0], args.password)
                token = auth_srvc.authenticate(credentials)
                print(token)
                f = open(file, "w")
                f.write(serialize(token))
                f.close()
            case 'validate':
                if not args.tokenPath:
                    raise ValueError("Token file path is required")
                f = open(args.tokenPath)
                token = deserialize(f.read())
                f.close()
                print(auth_srvc.validate_token(token))
            case 'get':
                if not args.tokenPath:
                    raise ValueError("Token file path is required")
                f = open(args.tokenPath)
                token = deserialize(f.read())
                f.close()
                print(user_db.get_user(ids[0], token))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
