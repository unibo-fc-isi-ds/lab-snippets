import shlex
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
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check','auth','shell'])
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
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                print(auth.authenticate(credentials))
            case 'shell':
                print("Commands: add/get/check/auth/exit")

                user_db = RemoteUserDatabase(args.address)
                auth = RemoteAuthenticationService(args.address)

                while True:
                    try:
                        line = input("lab4> ").strip()
                    except (EOFError, KeyboardInterrupt):
                        print()
                        break

                    if not line:
                        continue
                    if line in ('exit', 'quit'):
                        break
                    
                    parts = shlex.split(line) #per spazi nella password
                    cmd = parts[0]

                    try:
                        if cmd == 'add':
                            if len(parts) < 6:
                                raise ValueError("Usage: add <username> <email> <full_name...> <role:admin|user> <password>")
                            username = parts[1]
                            email = parts[2]
                            role = parts[-2].lower()
                            password = parts[-1]
                            full_name = " ".join(parts[3:-2])
                            user = User(username, [email], full_name, Role[role.upper()], password)
                            print(user_db.add_user(user))

                        elif cmd == 'get':
                            if len(parts) != 2:
                                raise ValueError("Usage: get <id>")
                            print(user_db.get_user(parts[1]))

                        elif cmd == 'check':
                            if len(parts) != 3:
                                raise ValueError("Usage: check <id> <password>")
                            creds = Credentials(parts[1], parts[2])
                            print(user_db.check_password(creds))

                        elif cmd == 'auth':
                            if len(parts) != 3:
                                raise ValueError("Usage: auth <id> <password>")
                            creds = Credentials(parts[1], parts[2])
                            token = auth.authenticate(creds)
                            print(token)
                            print("(token stored in client stub)")

                        else:
                            print("Unknown command. Use: add/get/check/auth/exit")

                    except RuntimeError as e:
                        print(f"[{type(e).__name__}]", *e.args)
                    except Exception as e:
                        print(f"[{type(e).__name__}]", str(e))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
