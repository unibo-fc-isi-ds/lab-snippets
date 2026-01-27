import argparse
import sys
import json
from datetime import timedelta

from .example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
from .users import User, Role, Credentials
from .example1_presentation import serialize, Deserializer, Token

# ==========================
# Глобальный токен для всех RPC-вызовов
# ==========================
RPC_TOKEN: Token | None = None

def main():
    global RPC_TOKEN

    parser = argparse.ArgumentParser(
        prog='python -m snippets.lab4.example4_rpc_client_cli',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password or token (use @file.json to load token from file)')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'login', 'validate'])

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    host, port = args.address.split(':')
    port = int(port)
    user_db = RemoteUserDatabase((host, port))
    auth_client = RemoteAuthenticationService((host, port))

    # ==========================
    # Передаём текущий токен в клиентов
    # ==========================
    user_db.rpc_token = RPC_TOKEN
    auth_client.rpc_token = RPC_TOKEN

    try:
        ids = (args.email or []) + ([args.user] if args.user else [])

        # ==== LOGIN ====
        if args.command == 'login':
            if not args.user or not args.password:
                raise ValueError("Username and password are required")
            credentials = Credentials(args.user, args.password)
            token = auth_client.authenticate(credentials)
            print(json.dumps(serialize(token), indent=2))
            # Сохраняем токен глобально
            RPC_TOKEN = token
            user_db.rpc_token = token
            auth_client.rpc_token = token
            return

        # ==== VALIDATE ====
        if args.command == 'validate':
            if not args.password:
                raise ValueError("Token required as --password")
            # ==== Поддержка токена из файла ====
            password_arg = args.password
            if password_arg.startswith('@'):
                with open(password_arg[1:], 'r', encoding='utf-8') as f:
                    password_arg = f.read()
            token_ast = json.loads(password_arg)
            token: Token = Deserializer()._ast_to_token(token_ast)
            valid = auth_client.validate_token(token)
            print(f"Token valid: {valid}")
            RPC_TOKEN = token
            user_db.rpc_token = token
            auth_client.rpc_token = token
            return

        # Для остальных команд проверяем наличие токена
        if not RPC_TOKEN:
            raise PermissionError("You must login first to use this command")

        match args.command:
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
                if not ids:
                    raise ValueError("Username or email is required")
                user = user_db.get_user(ids[0])
                print(user.copy(password=None))

            case 'check':
                if not args.password:
                    raise ValueError("Password required for check")
                credentials = Credentials(ids[0], args.password)
                result = user_db.check_password(credentials)
                print(f"Password correct: {result}")

    except Exception as e:
        print(f"[{type(e).__name__}]", *e.args)


if __name__ == '__main__':
    main()
