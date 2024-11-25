from .example3_rpc_client import *
import argparse
import sys
import json
import os
from datetime import timedelta


class TokenManager:
    @staticmethod
    def save_token(token: Token, filepath: str):
        """Save the token to a file"""
        with open(filepath, 'w') as f:
            f.write(serialize(token))

    @staticmethod
    def load_token(filepath: str) -> Token:
        """Load the token from a file"""
        with open(filepath, 'r') as f:
            return deserialize(f.read())


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database and authentication service',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'auth', 'validate', 'get'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token', '-t', help='Token for validation in JSON format')
    parser.add_argument('--token-file', '-f', help='Path to JSON file containing the token for validation')
    parser.add_argument('--save-token', '-s', help='Path to save the token JSON after authentication')

    # Parse the command-line arguments
    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    # Parse server address and instantiate clients
    server_address = address(args.address)
    user_db = RemoteUserDatabase(server_address)
    auth_service = RemoteAuthenticationService(server_address)

    # Load saved token if specified
    if args.token_file and os.path.exists(args.token_file):
        try:
            token = TokenManager.load_token(args.token_file)
            user_db.set_auth_token(token)
            auth_service.set_auth_token(token)
        except Exception as e:
            print(f"Error loading token from file {args.token_file}: {e}")
            sys.exit(1)

    try:
        # Match command and perform corresponding actions
        match args.command:
            case 'add':
                # Add a user to the database
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                if not args.user and not args.email:
                    raise ValueError("Username or email is required")
                user = User(
                    username=args.user,
                    emails=set(args.email) if args.email else set(),
                    full_name=args.name,
                    role=Role[args.role.upper()] if args.role else Role.USER,
                    password=args.password,
                )
                print(user_db.add_user(user))

            case 'auth':
                # Authenticate a user and save the token if requested
                if not args.password:
                    raise ValueError("Password is required")
                if not args.user and not args.email:
                    raise ValueError("Username or email is required")
                credentials = Credentials(
                    id=args.user or args.email[0],
                    password=args.password
                )
                duration = timedelta(days=1)  # Default token validity period
                token = auth_service.authenticate(credentials, duration)

                # Print the generated token
                print(token)

                # Save the token if --save-token is specified
                if args.save_token:
                    TokenManager.save_token(token, args.save_token)
                    print(f'Token saved to {args.save_token}')
                user_db.set_auth_token(token)
                auth_service.set_auth_token(token)

            case 'validate':
                # Validate a token
                if args.token_file and os.path.exists(args.token_file):
                    token = TokenManager.load_token(args.token_file)
                elif args.token:
                    token = deserialize(args.token)
                else:
                    raise ValueError("Either a token or a token file must be provided")
                print(auth_service.validate_token(token))

            case 'get':
                # Get user information (requires admin authorization)
                if not args.user:
                    raise ValueError("Username is required")
                try:
                    user = user_db.get_user(args.user)
                    print(user)
                except RuntimeError as e:
                    print(f"Error: {e}")

            case _:
                raise ValueError(f"Invalid command '{args.command}'")

    except Exception as e:
        print(f'Error: {e}')
