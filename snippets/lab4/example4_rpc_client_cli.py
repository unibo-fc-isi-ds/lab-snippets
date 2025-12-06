import argparse
import sys
import json
from datetime import timedelta

from .example3_rpc_client import RemoteUserDatabase, User, Role, Credentials
from snippets.lab4.example3_rpc_client import RemoteAuthenticationService
from snippets.lab4.example1_presentation import serialize, Deserializer, Token, User as PresUser

def main():
    parser = argparse.ArgumentParser(
        prog='python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password or token')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'login', 'validate'])

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    server_address = args.address.split(':')
    host = server_address[0]
    port = int(server_address[1])
    user_db = RemoteUserDatabase((host, port))
    auth_client = RemoteAuthenticationService((host, port))

    try:
        ids = (args.email or []) + ([args.user] if args.user else [])
        if not ids and args.command not in ['login', 'validate', 'add']:
            raise ValueError("Username or email address is required")

        match args.command:
            case 'login':
                if not args.user or not args.password:
                    raise ValueError("Username and password are required")
                credentials = Credentials(args.user, args.password)
                token = auth_client.authenticate(credentials)
                print(json.dumps(serialize(token), indent=2))

            case 'validate':
                if not args.password:
                    raise ValueError("Token required as --password")
                token_ast = json.loads(args.password)
                token: Token = Deserializer()._ast_to_token(token_ast)
                valid = auth_client.validate_token(token)
                print(f"Token valid: {valid}")

            case 'add':
                if not args.user or not args.password or not args.name:
                    raise ValueError("Username, full name, and password are required")
                user = User(
                    username=args.user,
                    emails=set(args.email or []),
                    full_name=args.name,
                    role=Role[args.role.upper()] if args.role else Role.USER,
                    password=args.password
                )
                user_db.add_user(user)
                print(f"Added user: {user.copy(password=None)}")


            case 'get':
                user = user_db.get_user(ids[0])
                print(user.copy(password=None))

            case 'check':
                if not args.password:
                    raise ValueError("Password required for check")
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))

    except Exception as e:
        print(f"[{type(e).__name__}]", *e.args)


if __name__ == '__main__':
    main()
