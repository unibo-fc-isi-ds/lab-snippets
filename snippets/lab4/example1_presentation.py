from .users import User, Credentials, Token, Role
from datetime import datetime, timedelta
import json
from dataclasses import dataclass


@dataclass
class Request:
    name: str
    args: tuple
    metadata: dict | None = None

    def __post_init__(self):
        self.args = tuple(self.args)


@dataclass
class Response:
    result: object | None
    error: str | None
    metadata: dict | None = None


class Serializer:
    primitive_types = (int, float, str, bool, type(None))
    container_types = (list, set)

    def serialize(self, obj):
        return self._ast_to_string(self._to_ast(obj))

    def _ast_to_string(self, data):
        return json.dumps(data, indent=2)

    def _to_ast(self, obj):
        if isinstance(obj, self.primitive_types):
            return obj
        if isinstance(obj, self.container_types):
            return [self._to_ast(item) for item in obj]
        if isinstance(obj, dict):
            return {key: self._to_ast(value) for key, value in obj.items()}
        # Метод для кастомных типов
        method_name = f'_{type(obj).__name__.lower()}_to_ast'
        if hasattr(self, method_name):
            data = getattr(self, method_name)(obj)
            data['$type'] = type(obj).__name__
            return data
        raise ValueError(f"Unsupported type {type(obj)}")

    # ===== User / Credentials / Token / Role / Request / Response =====
    def _user_to_ast(self, user: User):
        return {
            'username': self._to_ast(user.username),
            'emails': [self._to_ast(email) for email in user.emails],
            'full_name': self._to_ast(user.full_name),
            'role': self._to_ast(user.role),
            'password': self._to_ast(user.password),
        }

    def _credentials_to_ast(self, credentials: Credentials):
        return {
            'id': self._to_ast(credentials.id),
            'password': self._to_ast(credentials.password),
        }

    def _token_to_ast(self, token: Token):
        return {
            'signature': self._to_ast(token.signature),
            'user': self._to_ast(token.user),
            'expiration': self._to_ast(token.expiration),
        }

    def _datetime_to_ast(self, dt: datetime):
        return {'value': dt.isoformat()}

    def _timedelta_to_ast(self, td: timedelta):
        # Сериализуем как количество секунд
        return {'seconds': td.total_seconds()}

    def _role_to_ast(self, role: Role):
        return {'name': role.name}

    def _request_to_ast(self, request: Request):
        return {
            'name': self._to_ast(request.name),
            'args': [self._to_ast(arg) for arg in request.args],
            'metadata': self._to_ast(request.metadata) if request.metadata else None,
        }


    def _response_to_ast(self, response: Response):
        return {
            'result': self._to_ast(response.result) if response.result is not None else None,
            'error': self._to_ast(response.error),
        }


class Deserializer:
    def deserialize(self, string):
        return self._ast_to_obj(self._string_to_ast(string))

    def _string_to_ast(self, string):
        return json.loads(string)

    def _ast_to_obj(self, data):
        if isinstance(data, dict):
            if '$type' not in data:
                return {key: self._ast_to_obj(value) for key, value in data.items()}
            method_name = f'_ast_to_{data["$type"].lower()}'
            if hasattr(self, method_name):
                return getattr(self, method_name)(data)
            raise ValueError(f"Unsupported type {data['$type']}")
        if isinstance(data, list):
            return [self._ast_to_obj(item) for item in data]
        return data

    # ===== User / Credentials / Token / Role / Request / Response =====
    def _ast_to_user(self, data):
        return User(
            username=str(self._ast_to_obj(data['username'])),
            emails=set(map(str, self._ast_to_obj(data['emails']))),
            full_name=str(self._ast_to_obj(data['full_name'])) if self._ast_to_obj(data['full_name']) is not None else None,
            role=self._ast_to_role(data['role']),
            password=str(self._ast_to_obj(data['password'])),
        )



    def _ast_to_credentials(self, data):
        return Credentials(
            id=str(self._ast_to_obj(data['id'])),
            password=str(self._ast_to_obj(data['password'])),
        )


    def _ast_to_token(self, data):
        return Token(
            signature=str(self._ast_to_obj(data['signature'])),
            user=self._ast_to_user(self._ast_to_obj(data['user'])),  # используем метод _ast_to_user
            expiration=self._ast_to_datetime(self._ast_to_obj(data['expiration'])),  # используем _ast_to_datetime
        )


    def _ast_to_datetime(self, data):
        return datetime.fromisoformat(data['value'])

    def _ast_to_timedelta(self, data):
        return timedelta(seconds=data['seconds'])

    def _ast_to_role(self, data):
        return Role[str(self._ast_to_obj(data['name']))]

    def _ast_to_request(self, data):
        metadata = self._ast_to_obj(data['metadata']) if 'metadata' in data and data['metadata'] is not None else None
        if metadata is not None and not isinstance(metadata, dict):
            raise ValueError(f"Expected dict or None for metadata, got {type(metadata)}")
        return Request(
            name=str(self._ast_to_obj(data['name'])),
            args=tuple(self._ast_to_obj(arg) for arg in data['args']),
            metadata=metadata,
        )



    def _ast_to_response(self, data):
        return Response(
            result=self._ast_to_obj(data['result']) if data['result'] is not None else None,
            error=str(self._ast_to_obj(data['error'])) if data['error'] is not None else None,
        )



DEFAULT_SERIALIZER = Serializer()
DEFAULT_DESERIALIZER = Deserializer()


def serialize(obj):
    return DEFAULT_SERIALIZER.serialize(obj)


def deserialize(string):
    return DEFAULT_DESERIALIZER.deserialize(string)

