import argparse
import sys

from .example3_rpc_client import *

if __name__ == "__main__":

    parser = argparse.ArgumentParser(
        prog=f"python -m snippets -l 4 -e 4",
        description="RPC client for user database",
        exit_on_error=False,
    )
    parser.add_argument("address", help="Server address in the form ip:port")
    parser.add_argument(
        "command",
        help="Method to call",
        choices=["add", "get", "check", "authenticate", "validate_token"],
    )
    parser.add_argument("--user", "-u", help="Username")
    parser.add_argument("--email", "--address", "-a", nargs="+", help="Email address")
    parser.add_argument("--name", "-n", help="Full name")
    parser.add_argument(
        "--role", "-r", help='Role (defaults to "user")', choices=["admin", "user"]
    )
    parser.add_argument("--password", "-p", help="Password")
    parser.add_argument(
        "--duration",
        "-d",
        help="Token duration (in seconds), defaults to 1 day",
        type=int,
        required=False,
        default=86400,
    )
    parser.add_argument(
        "--token",
        "-t",
        help="File name in which to save the token, defaults to 'token.json'",
        type=str,
        required=False,
        default="token.json",
    )

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    try:
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        match args.command:
            case "add":
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(
                    args.user,
                    args.email,
                    args.name,
                    Role[args.role.upper()],
                    args.password,
                )
                print(user_db.add_user(user))
            case "get":
                print(user_db.get_user(ids[0]))
            case "check":
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case "authenticate":
                credentials = Credentials(ids[0], args.password)
                duration = timedelta(seconds=args.duration)
                print(duration)
                token = auth_service.authenticate(credentials, duration)
                with open(args.token, "w") as f:
                    f.write(serialize(token))
                print(f"Token saved to {args.token}")
            case "validate_token":
                with open(args.token, "r") as f:
                    content = f.read()
                token = deserialize(content)
                print(
                    f"The token validation request returned: {auth_service.validate_token(token)}"
                )

            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f"[{type(e).__name__}]", *e.args)
