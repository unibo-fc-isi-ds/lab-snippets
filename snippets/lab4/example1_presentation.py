from .users import User, Credentials, Token, Role
from datetime import datetime
import json
from dataclasses import dataclass


@dataclass
class Request:
    """
    A container for RPC requests: function name and its arguments.
    """
    name: str
    args: tuple
    metadata: object | None = None

    def __post_init__(self):
        self.args = tuple(self.args)


@dataclass
class Response:
    """
    A container for RPC responses: function result or an error message.
    """
    result: object | None = None
    error: str | None = None


class Serializer:
    PRIMITIVE_TYPES = (int, float, str, bool, type(None))
    CONTAINER_TYPES = (list, set)

    def serialize(self, obj):
        return json.dumps(self._to_ast(obj), indent=2)

    def _to_ast(self, obj):
        if isinstance(obj, self.PRIMITIVE_TYPES):
            return obj
        if isinstance(obj, self.CONTAINER_TYPES):
            return [self._to_ast(item) for item in obj]
        if isinstance(obj, dict):
            return {key: self._to_ast(value) for key, value in obj.items()}
        method_name = f'_to_{type(obj).__name__.lower()}_ast'
        if hasattr(self, method_name):
            data = getattr(self, method_name)(obj)
            if isinstance(data, dict):
                data['$type'] = type(obj).__name__
            return data
        raise TypeError(f"Unsupported type: {type(obj)}")

    def _to_user_ast(self, user: User):
        return {
            'username': self._to_ast(user.username),
            'emails': [self._to_ast(email) for email in user.emails],
            'full_name': self._to_ast(user.full_name),
            'role': self._to_ast(user.role),
            'password': self._to_ast(user.password),
        }

    def _to_credentials_ast(self, credentials: Credentials):
        return {
            'id': self._to_ast(credentials.id),
            'password': self._to_ast(credentials.password),
        }

    def _to_token_ast(self, token: Token):
        return {
            'signature': self._to_ast(token.signature),
            'user': self._to_ast(token.user),
            'expiration': token.expiration.isoformat(),
        }

    def _to_role_ast(self, role: Role):
        return {'name': role.name}

    def _to_request_ast(self, request: Request):
        return {
            'name': self._to_ast(request.name),
            'args': [self._to_ast(arg) for arg in request.args],
            'metadata': self._to_ast(request.metadata),
        }

    def _to_response_ast(self, response: Response):
        return {
            'result': self._to_ast(response.result),
            'error': self._to_ast(response.error),
        }


class Deserializer:
    def deserialize(self, string):
        return self._from_ast(json.loads(string))

    def _from_ast(self, data):
        if isinstance(data, dict):
            if '$type' not in data:
                return {key: self._from_ast(value) for key, value in data.items()}
            method_name = f'_from_{data["$type"].lower()}_ast'
            if hasattr(self, method_name):
                return getattr(self, method_name)(data)
            raise TypeError(f"Unsupported type: {data['$type']}")
        if isinstance(data, list):
            return [self._from_ast(item) for item in data]
        return data

    def _from_user_ast(self, data):
        return User(
            username=self._from_ast(data['username']),
            emails=set(self._from_ast(data['emails'])),
            full_name=self._from_ast(data['full_name']),
            role=self._from_ast(data['role']),
            password=self._from_ast(data['password']),
        )

    def _from_credentials_ast(self, data):
        return Credentials(
            id=self._from_ast(data['id']),
            password=self._from_ast(data['password']),
        )

    def _from_token_ast(self, data):
        return Token(
            signature=self._from_ast(data['signature']),
            user=self._from_ast(data['user']),
            expiration=datetime.fromisoformat(data['expiration']),
        )

    def _from_role_ast(self, data):
        return Role[name=data['name']]

    def _from_request_ast(self, data):
        return Request(
            name=self._from_ast(data['name']),
            args=tuple(self._from_ast(arg) for arg in data['args']),
            metadata=self._from_ast(data.get('metadata')),
        )

    def _from_response_ast(self, data):
        return Response(
            result=self._from_ast(data['result']),
            error=self._from_ast(data['error']),
        )


DEFAULT_SERIALIZER = Serializer()
DEFAULT_DESERIALIZER = Deserializer()


def serialize(obj):
    return DEFAULT_SERIALIZER.serialize(obj)


def deserialize(string):
    return DEFAULT_DESERIALIZER.deserialize(string)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_wrong

    request = Request(
        name='my_function',
        args=(
            gc_credentials_wrong,
            gc_user,
            ["example", 42, 3.14, True, False],
            {'key': 'value'},
            Response(None, 'an error'),
        )
    )
    serialized = serialize(request)
    print("Serialized:", serialized)
    deserialized = deserialize(serialized)
    print("Deserialized:", deserialized)
    assert request == deserialized
