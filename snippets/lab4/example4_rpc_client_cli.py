import json
from snippets.lab4.example1_presentation import Serializer, Deserializer
from snippets.lab4.users.impl import InMemoryAuthenticationService
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

    TOKENS_FILE_NAME = "tokens.json"
    DEFAULT_SERIALIZER = Serializer()
    DEFAULT_DESERIALIZER = Deserializer()

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    authentication_service = RemoteAuthenticationService(args.address)

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
                    raise ValueError("Password is required")
                
                credentials = Credentials(ids[0], args.password)
                token = authentication_service.authenticate(credentials)

                try:
                    with open(TOKENS_FILE_NAME, 'r+') as file:
                        tokens = DEFAULT_DESERIALIZER.deserialize(file.read() or '[]')
                except (FileNotFoundError, ValueError):
                    tokens = []

                tokens = [t for t in tokens if t.user.username != token.user.username]
                print(f"n token letti: {len(tokens)}")
                tokens.append(token)

                with open(TOKENS_FILE_NAME, 'w') as file:
                    file.write(DEFAULT_SERIALIZER.serialize(tokens))
                # print(token)
            case 'validate':
                try:
                    with open(TOKENS_FILE_NAME, 'r') as file:
                        tokens = DEFAULT_DESERIALIZER.deserialize(file.read() or '[]')
                except (FileNotFoundError, ValueError):
                    tokens = []

                foundToken = None
                for t in tokens:
                    if t.user.username in ids:
                        foundToken = t
                        break
                if foundToken:
                    print(authentication_service.validate_token(t))
                else:
                    print(False)
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
