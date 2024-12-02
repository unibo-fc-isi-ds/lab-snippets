import os
from .example3_rpc_client import *
import argparse
import sys


if __name__ == '__main__':
    'poetry run python -m snippets -l 4 -e 4 127.0.0.1:5000 add --user nico --email "nicolo@email.com" --name Nicolo --role admin --password password'
    

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token-file', '-t', help='Authentication token file')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        token_file = args.token_file or 'token.txt'
        if os.path.exists(token_file):
            # Se il file esiste, leggi il token
            with open(token_file) as f:
                try:
                    token = deserialize(f.read())
                    if not isinstance(token, Token):
                        raise ValueError("Invalid token")
                except Exception as e:
                    print(f'[{type(e).__name__}]', *e.args)
                    token = None
        else:
            # Altrimenti, inizializza il token a None
            token = None
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user, token))
            case 'get':
                print(user_db.get_user(ids[0], token))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials, token))
            case 'authenticate':
                credentials = Credentials(args.user, args.password)
                token = user_db.authenticate(credentials)
                with open(token_file, 'w') as f:
                    f.write(serialize(token))
                print("Token saved to", token_file)
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
