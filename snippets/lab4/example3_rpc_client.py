from datetime import timedelta
import sys
import json

# Импорты из вашего пакета, Pyright теперь видит их после корректного __init__.py
from snippets.lab3 import Client  # pyright: ignore[reportMissingImports]
from snippets.lab4.users import User, Credentials, Token, Role, UserDatabase, AuthenticationService  # pyright: ignore[reportMissingImports]
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response, Deserializer  # pyright: ignore[reportMissingImports]


class ClientStub:
    def __init__(self, server_address: tuple[str, int]):
        host, port = server_address
        self.__server_address = (host, int(port))
        self.rpc_token: Token | None = None  # Токен для авторизации защищённых методов

    def rpc(self, name: str, *args):
        client = Client(self.__server_address)
        try:
            # Передаём токен только для защищённых методов
            protected_methods = ["add_user", "get_user", "check_password"]
            metadata = self.rpc_token if name in protected_methods else None
            request = Request(name, args, metadata=metadata)
            request_serialized = serialize(request)
            client.send(request_serialized)
            response_serialized = client.receive()
            response = deserialize(response_serialized)
            if response.error:
                raise RuntimeError(response.error)
            return response.result
        finally:
            client.close()


class RemoteUserDatabase(ClientStub, UserDatabase):
    def add_user(self, user: User):
        return self.rpc('add_user', user)

    def get_user(self, id: str) -> User:
        return self.rpc('get_user', id)

    def check_password(self, credentials: Credentials) -> bool:
        return self.rpc('check_password', credentials)


class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def authenticate(self, credentials: Credentials, duration: timedelta | None = None) -> Token:
        if duration is None:
            duration = timedelta(hours=1)
        # Получаем токен и сохраняем для последующих вызовов
        token: Token = self.rpc("authenticate", credentials, duration)
        self.rpc_token = token
        return token

    def validate_token(self, token: Token) -> bool:
        return self.rpc("validate_token", token)


def main():
    if len(sys.argv) < 4:
        print("Usage: python -m snippets.lab4.example3_rpc_client <host:port> <command> key=value ...")
        sys.exit(1)

    host_port = sys.argv[1]
    if ':' not in host_port:
        raise ValueError("Address must be in form ip:port, e.g. 127.0.0.1:12345")
    host, port_str = host_port.split(':')
    port = int(port_str)
    command = sys.argv[2]

    user_db = RemoteUserDatabase((host, port))
    auth_client = RemoteAuthenticationService((host, port))
    auth_token: Token | None = None

    # ===== Разбираем ключ=значение =====
    args_map = {}
    for arg in sys.argv[3:]:
        if '=' not in arg:
            continue
        key, value = arg.split('=', 1)
        args_map[key] = value

    user = args_map.get('user')
    password = args_map.get('password')
    name = args_map.get('name')
    emails = args_map.get('emails')
    role = args_map.get('role', 'user')
    emails_set = set(emails.split(',')) if emails else set()

    try:
            # ========= Логин / Получение токена =========
            if command in ['login', 'login-validate']:
                if not user or not password:
                    raise ValueError(f"{command} requires user and password")
                credentials = Credentials(user, password)
                token = RemoteAuthenticationService((host, port)).authenticate(credentials)
                auth_token = token
                print("Token:", json.dumps(serialize(token), indent=2))

                if command == 'login-validate':
                    valid = RemoteAuthenticationService((host, port)).validate_token(token)
                    print("Token valid:", valid)
                return  # После логина/валидации завершаем

            # ========= Проверка токена для защищённых команд =========
            if command in ['add', 'get', 'check']:
                if not auth_token:
                    raise ValueError("You must login first to get a token")
                user_db = RemoteUserDatabase((host, port))
                # Передаём токен в metadata при RPC
                user_db.rpc_metadata = auth_token

            # ========= Обработка команд =========
            if command == 'add':
                if not user or not password or not name:
                    raise ValueError("add requires user, password, and name")
                new_user = User(
                    username=user,
                    emails=emails_set,
                    full_name=name,
                    role=Role[role.upper()] if role else Role.USER,
                    password=password
                )
                result = user_db.add_user(new_user)
                print("Added user:", result)

            elif command == 'get':
                if not user:
                    raise ValueError("get requires user")
                result = user_db.get_user(user)
                print("User info:", result)

            elif command == 'check':
                if not user or not password:
                    raise ValueError("check requires user and password")
                credentials = Credentials(user, password)
                result = user_db.check_password(credentials)
                print("Password correct:", result)

            elif command == 'validate':
                if not password:
                    raise ValueError("validate requires token in password")
                token_ast = json.loads(password)
                token = Deserializer()._ast_to_token(token_ast)
                valid = RemoteAuthenticationService((host, port)).validate_token(token)
                print("Token valid:", valid)

            else:
                raise ValueError(f"Unknown command {command}")

    except RuntimeError as e:
        print(f"RuntimeError:", e)
    except Exception as e:
        print(f"Error:", e)


if __name__ == '__main__':
    main()
