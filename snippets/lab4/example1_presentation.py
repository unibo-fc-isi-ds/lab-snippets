from .users import User, Credentials, Token, Role
from datetime import datetime
import json
from dataclasses import dataclass


@dataclass
class Request:
    """
    A container for RPC requests: a name of the function to call and its arguments.
    """

    name: str
    args: tuple
    metadata: object | None

    def __post_init__(self):
        self.args = tuple(self.args)


@dataclass
class Response:
    """
    A container for RPC responses: a result of the function call or an error message.
    When error is None, it means there was no error.
    Result may be None, if the function returns None.
    """

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
        # selects the appropriate method to convert the object to AST via reflection
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
        return {'datetime': dt.isoformat()}

    def _role_to_ast(self, role: Role):
        return {'name': role.name}

    def _request_to_ast(self, request: Request):
        return {
            'name': self._to_ast(request.name),
            'args': [self._to_ast(arg) for arg in request.args],
            'metadata': self._to_ast(request.metadata)
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
            # selects the appropriate method to convert the AST to object via reflection
            method_name = f'_ast_to_{data["$type"].lower()}'
            if hasattr(self, method_name):
                return getattr(self, method_name)(data)
            raise ValueError(f"Unsupported type {data['type']}")
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
            expiration=self._ast_to_obj(data['expiration']),
        )

    def _ast_to_datetime(self, data):
        print(data['datetime'])
        return datetime.fromisoformat(data['datetime'])

    def _ast_to_role(self, data):
        return Role[self._ast_to_obj(data['name'])]

    def _ast_to_request(self, data):
        return Request(
            name=self._ast_to_obj(data['name']),
            args=tuple(self._ast_to_obj(arg) for arg in data['args']),
            metadata=self._ast_to_obj(data['metadata'])
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


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_wrong

    request = Request(
        name='my_function',
        args=(
            gc_credentials_wrong, # an instance of Credentials
            gc_user, # an instance of User
            ["a string", 42, 3.14, True, False], # a list, containing various primitive types
            {'key': 'value'}, # a dictionary
            Response(None, 'an error'), # a Response, which contains a None field
        )
    )
    serialized = serialize(request)
    print("Serialized", "=", serialized)
    deserialized = deserialize(serialized)
    print("Deserialized", "=", deserialized)
    assert request == deserialized
