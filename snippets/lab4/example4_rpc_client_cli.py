from .example3_rpc_client import *
import argparse
import sys
import json

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database and authentication service',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'auth', 'validate'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--token', '-t', help='Token for validation in JSON format')
    parser.add_argument('--token-file', '-f', help='Path to JSON file containing the token for validation')
    parser.add_argument('--save-token', '-s', help='Path to save the token JSON after authentication')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    auth_service = RemoteAuthenticationService(args.address)

    try:
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                print(user_db.get_user(args.user or args.email[0]))
            case 'check':
                credentials = Credentials(args.user or args.email[0], args.password)
                print(user_db.check_password(credentials))
            case 'auth':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(args.user or args.email[0], args.password)
                duration = timedelta(days=1)  # 默认给定一个1天的有效期
                token = auth_service.authenticate(credentials, duration)
                
                # 输出 token
                print(token)

                # 如果提供了 --save-token 参数，将令牌保存为 JSON 文件
                if args.save_token:
                    with open(args.save_token, 'w') as token_file:
                        serialized_token = serialize(token)  # 将 Token 序列化为 JSON 字符串
                        token_file.write(serialized_token)
                    print(f'Token saved to {args.save_token}')
            case 'validate':
                if args.token:
                    # 如果通过 -t 参数直接传递了令牌，则进行反序列化
                    token = deserialize(args.token)
                elif args.token_file:
                    # 如果通过 -f 参数传递了令牌文件路径，则从文件中读取并反序列化
                    with open(args.token_file, 'r') as file:
                        token_data = file.read()
                        token = deserialize(token_data)
                else:
                    raise ValueError("Either a token or a token file must be provided")
                
                # 验证 token
                print(auth_service.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
