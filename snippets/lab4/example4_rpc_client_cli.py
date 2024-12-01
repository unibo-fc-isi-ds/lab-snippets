from .example3_rpc_client import *
import argparse
import sys
import os

def parse_timedelta(value):
    try:
        days = hours = minutes = 0
        if 'd' in value:
            days, value = value.split('d')
            days = int(days)
        if 'h' in value:
            hours, value = value.split('h')
            hours = int(hours)
        if 'm' in value:
            minutes = int(value.split('m')[0])
        return timedelta(days=days, hours=hours, minutes=minutes)
    except Exception as e:
        raise argparse.ArgumentTypeError(f"Invalid timedelta format: {value}. Expected something like '1d2h30m'.")

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

    parser.add_argument('--duration', '-d', type=parse_timedelta, help="Token duration formatted as (\d+d)?(\d+h)?(\dm)?")
    parser.add_argument('--save_token_path', '-s', default="./snippets/lab4/gen_token/", help="Path to save token json file")
    parser.add_argument('--load_token_path', '-t', default="./snippets/lab4/gen_token/token.json", help="Path to load token json file")

    

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    user_auth_service = RemoteAuthenticationService(args.address)

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
                if not args.duration:
                    raise ValueError("Token duration is required")
                credentials = Credentials(ids[0], args.password)
                token_obj = user_auth_service.authenticate(credentials, args.duration)  
                token_ast_json = serialize(token_obj)
                #save json file to current directory
                with open(args.save_token_path + "token.json", "w") as f:
                    f.write(token_ast_json)
            case 'validate':
                if not os.path.exists(args.load_token_path):
                    raise FileNotFoundError(f"The file {args.load_token_path} does not exist.")

                with open(args.load_token_path, "r") as f:
                    token_ast_json = f.read()

                token_obj = deserialize(token_ast_json)
                print(user_auth_service.validate_token(token_obj))
            case _: 
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
