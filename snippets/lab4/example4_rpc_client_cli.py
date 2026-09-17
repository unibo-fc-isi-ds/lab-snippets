from .example3_rpc_client import *
import argparse
import sys
from datetime import timedelta
import json


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database and authentication service',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check' ,'authenticate', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')

    parser.add_argument("--duration", "-d", type=int, help="Token duration (seconds)")
    parser.add_argument("--token", "-t", help="Path to token file (JSON)")

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
        commands_requiring_ids  = ['add', 'get', 'check' ,'authenticate']
        if len(ids) == 0 and args.command in commands_requiring_ids:
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
                credentials = Credentials(ids[0], args.password)
                duration = timedelta(seconds=args.duration) if args.duration is not None else None
                token = auth_service.authenticate(credentials, duration)
                print(token)
                token_file = args.token if args.token is not None else f"token-{datetime.now().timestamp()}.json"
                with open(token_file,"w") as f:
                    f.write(serialize(token))
                    print(f"Token written to file {token_file}")
            case 'validate':
                if not args.token:
                    raise ValueError("Token file is required")
                with open(args.token, "r") as f:
                    buf = f.read()
                token = deserialize(buf)
                print(auth_service.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
