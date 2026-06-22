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
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate', 'validate', 'token'])   #the new valid commands are: authenticate, to authenticate a registered user, validate, to check the validity the token provided by the user via cli, and token, to get the token of the user performing the request.
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--signature', '-s', help='Signature of Token')
    parser.add_argument('--duration', '-d', help='Duration of token')
    parser.add_argument('--expiration', '-e', help='Expiration of Token')
    parser.add_argument('--user_to_get', '-g', help='Username of the user\'s data that the client wants to read')


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
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], password = args.password)
                print(user_db.add_user(user))
            case 'get':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.user_to_get:
                    raise ValueError("Username of the user to get required")
                credentials = Credentials(ids[0], args.password)
                if user_db.check_password(credentials): #an authenticated user that is admin can read the data of another user only if his password is correct, meaning that he's actually the one making the request
                    print(user_db.get_user(args.user_to_get, args.user)) #now, get_user requires 2 arguments: the username of the user whose data the client wants to read, and the user performing the request
                else: raise ValueError("Invalid credentials")
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                credentials = Credentials(ids[0], args.password)
                if args.duration:
                    duration = timedelta(seconds=int(args.duration)) #we need to convert the cli arguments (str) into the correct types - timedelta for duration
                else:
                    duration: timedelta = None
                print(auth_service.authenticate(credentials, duration))
            case 'validate':
                if not args.expiration:
                    raise ValueError("Expiration is required")
                if not args.signature:
                    raise ValueError("Signature is required")
                expiration_dt = datetime.fromisoformat(args.expiration) #we need to convert the cli arguments (str) into the correct types - datetime for expiration
                user = User(args.user, args.email, args.name, Role[args.role.upper()], password = None)
                token = Token(
                    user = user,
                    expiration=expiration_dt,
                    signature=args.signature
                )                
                print(auth_service.validate_token(token))
            case 'token':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                if user_db.check_password(credentials):
                    print(auth_service.get_token(ids[0]))
                else: 
                    raise ValueError("Invalid credentials")
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
