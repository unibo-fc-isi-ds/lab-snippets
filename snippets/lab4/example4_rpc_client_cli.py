# https://unibo-fc-isi-ds.github.io/slides-module2/presentation/#/exercise-rpc-auth-service-secure
#
# Authenticate command:
# python -m snippets -l 4 -e 4 SERVER_IP:PORT auth -u gciatto -p "my secret password" -d 300 -o token.json
#
# Validate command:
# python -m snippets -l 4 -e 4 SERVER_IP:PORT valid -i token.json


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
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'auth', 'valid'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--duration', '-d', help='Duration of token in seconds')
    parser.add_argument('--output', '-o', help='Output file for received token')
    parser.add_argument('--input', '-i', help='Input token file')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    token = None

    try:
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        if args.input:
            with open(args.input, 'rt') as f:
                token = deserialize(f.read())
        user_db = RemoteUserDatabase(args.address, token)
        auth_service = RemoteAuthenticationService(args.address, token)
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
                duration = timedelta(seconds=args.duration) if args.duration is not None else None
                token = auth_service.authenticate(credentials, duration)
                with open(args.output, 'wt') as f:
                    f.write(serialize(token))
            case 'valid':
                print(auth_service.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
