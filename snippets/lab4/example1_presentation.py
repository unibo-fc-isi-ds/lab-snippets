from .users import User, Credentials, Token, Role
from datetime import datetime, timedelta
import json
from dataclasses import dataclass

@dataclass
class Request:
    name: str
    args: tuple
    metadata: dict | None = None  # Add metadata field to pass the token

    def __post_init__(self):
        self.args = tuple(self.args)
        if self.metadata is None:
            self.metadata = {}


@dataclass
class Response:
    result: object | None
    error: str | None


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
        method_name = f'_{type(obj).__name__.lower()}_to_ast'
        if hasattr(self, method_name):
            data = getattr(self, method_name)(obj)
            data['$type'] = type(obj).__name__
            return data
        raise ValueError(f"Unsupported type {type(obj)}")

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
        return {
            'iso': dt.isoformat(),
            '$type': 'datetime'
        }

    def _timedelta_to_ast(self, td: timedelta):
        return {
            'days': td.days,
            'seconds': td.seconds,
            'microseconds': td.microseconds,
            '$type': 'timedelta'
        }

    def _role_to_ast(self, role: Role):
        return {'name': role.name}

    def _request_to_ast(self, request: Request):
        return {
            'name': self._to_ast(request.name),
            'args': [self._to_ast(arg) for arg in request.args],
            'metadata': self._to_ast(request.metadata) if request.metadata is not None else None,
        }

    def _response_to_ast(self, response: Response):
        return {
            'result': self._to_ast(response.result) if response.result is not None else None,
            'error': self._to_ast(response.error),
        }


class Deserializer:
    def deserialize(self, string):
        return self._ast_to_obj(json.loads(string))

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

    def _ast_to_user(self, data):
        return User(
            username=self._ast_to_obj(data['username']),
            emails=set(self._ast_to_obj(data['emails'])),
            full_name=self._ast_to_obj(data['full_name']),
            role=self._ast_to_obj(data['role']),
            password=self._ast_to_obj(data['password']),
        )

    def _ast_to_credentials(self, data):
        return Credentials(
            id=self._ast_to_obj(data['id']),
            password=self._ast_to_obj(data['password']),
        )

    def _ast_to_token(self, data):
        return Token(
            signature=self._ast_to_obj(data['signature']),
            user=self._ast_to_obj(data['user']),
            expiration=datetime.fromisoformat(self._ast_to_obj(data['expiration']['iso']))
        )

    def _ast_to_datetime(self, data):
        return datetime.fromisoformat(data['iso'])

    def _ast_to_timedelta(self, data):
        return timedelta(
            days=data['days'],
            seconds=data['seconds'],
            microseconds=data['microseconds']
        )

    def _ast_to_role(self, data):
        return Role[data['name']]

    def _ast_to_request(self, data):
        return Request(
            name=self._ast_to_obj(data['name']),
            args=tuple(self._ast_to_obj(arg) for arg in data['args']),
            metadata=self._ast_to_obj(data['metadata']) if data['metadata'] is not None else None,
        )

    def _ast_to_response(self, data):
        return Response(
            result=self._ast_to_obj(data['result']) if data['result'] is not None else None,
            error=self._ast_to_obj(data['error']),
        )


DEFAULT_SERIALIZER = Serializer()
DEFAULT_DESERIALIZER = Deserializer()

def serialize(obj):
    return DEFAULT_SERIALIZER.serialize(obj)

def deserialize(string):
    return DEFAULT_DESERIALIZER.deserialize(string)
