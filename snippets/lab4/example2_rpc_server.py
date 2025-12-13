
import sys
import traceback

from snippets.lab3 import Server # pyright: ignore[reportMissingImports]
from snippets.lab4.users.impl import InMemoryUserDatabase # pyright: ignore[reportMissingImports]
from snippets.lab4.example1_presentation import Role, serialize, deserialize, Request, Response  # pyright: ignore[reportMissingImports]
from snippets.lab4.users.auth_impl import InMemoryAuthenticationService  # pyright: ignore[reportMissingImports]
from .example0_users import load_default_users
from .users import Token


class AuthenticationServerStub:
    def __init__(self, auth_service: InMemoryAuthenticationService):
        self.auth_service = auth_service

    def handle_request(self, request: Request) -> Response:
        try:
            if request.name == "authenticate":
                credentials, duration = request.args
                result = self.auth_service.authenticate(credentials, duration)
                error = None
            elif request.name == "validate_token":
                token, = request.args
                result = self.auth_service.validate_token(token)
                error = None
            else:
                result = None
                error = f"Unknown method: {request.name}"
        except Exception as e:
            result = None
            error = " ".join(str(arg) for arg in e.args)
        return Response(result, error)


class ServerStub(Server):
    def __init__(self, port: int):
        super().__init__(port, self.__on_connection_event)
        self.__user_db = InMemoryUserDatabase()
        load_default_users(self.__user_db)
        self.auth_service = InMemoryAuthenticationService(self.__user_db)
        self.auth_stub = AuthenticationServerStub(self.auth_service)

    def __on_connection_event(self, event, connection, address, error):
        match event:
            case "listen":
                print(f"Server listening on {address[0]}:{address[1]}")
            case "connect":
                connection.callback = self.__on_message_event
            case "error":
                traceback.print_exception(type(error), error, error.__traceback__)
            case "stop":
                print("Server stopped")

    def __on_message_event(self, event, payload, connection, error):
        match event:
            case "message":
                print(f"[{connection.remote_address}] Open connection")
                request = deserialize(payload)
                assert isinstance(request, Request)
                print(f"[{connection.remote_address}] Unmarshalled request:", request)

                # Получаем Response
                response = self.__handle_request(request)

                # === Исправление: если результат Token, конвертируем в dict ===
                if isinstance(response.result, Token):
                    response = Response(response.result.to_dict(), response.error)

                connection.send(serialize(response))
                print(f"[{connection.remote_address}] Marshalled response:", response)
                connection.close()

            case "error":
                traceback.print_exception(type(error), error, error.__traceback__)
            case "close":
                print(f"[{connection.remote_address}] Close connection")

    def __handle_request(self, request: Request) -> Response:
        try:
            # ==== Список защищённых методов ====
            protected_methods = ["add_user", "get_user", "check_password"]

            if request.name in protected_methods:
                # Получаем токен из request.metadata
                token = getattr(request, 'metadata', None)
                if token is None:
                    return Response(None, "Authentication required")

                if not self.auth_service.validate_token(token):
                    return Response(None, "Invalid or expired token")

                # Проверка роли для метода get_user
                if request.name == "get_user" and token.user.role != Role.ADMIN:
                    return Response(None, "Admin role required")

                # Выполняем метод базы данных
                method = getattr(self.__user_db, request.name)
                result = method(*request.args)
                return Response(result, None)

            # ==== Методы аутентификации ====
            elif request.name in ["authenticate", "validate_token"]:
                return self.auth_stub.handle_request(request)

            else:
                return Response(None, f"Unknown method: {request.name}")

        except Exception as e:
            # Любые другие ошибки возвращаем клиенту
            return Response(None, str(e))




if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python -m snippets.lab4.example2_rpc_server <port>")
        sys.exit(1)

    port = int(sys.argv[1])
    server = ServerStub(port)
    try:
        input("Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n")
    except (EOFError, KeyboardInterrupt):
        pass
    server.close()
