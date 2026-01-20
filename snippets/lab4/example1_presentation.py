from .users import User, Credentials, Token, Role
from datetime import datetime, timedelta
import json
from dataclasses import dataclass


@dataclass
class Request:
    """
    A container for RPC requests: a name of the function to call and its arguments.
    """

    name: str
    args: tuple
    metadata: dict | None = None

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


        result = None

        if isinstance(obj, User):
            result = self._user_to_ast(obj)
        elif isinstance(obj, Role):
            result = self._role_to_ast(obj)
        elif isinstance(obj, Credentials):
            result = self._credentials_to_ast(obj)
        elif isinstance(obj, Token):
            result = self._token_to_ast(obj)
        elif isinstance(obj, timedelta):
            result = self._timedelta_to_ast(obj)
        elif isinstance(obj, datetime):
            return obj.isoformat()  # datetime without $type, it's a string
        elif isinstance(obj, Request):
            result = self._request_to_ast(obj)
        elif isinstance(obj, Response):
            result = self._response_to_ast(obj)
        else:
            raise ValueError(f'Cannot serialize object of type {type(obj)}')

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

    def _timedelta_to_ast(self, td: timedelta) -> dict:
        """Converts timedelta to dict (AST)"""
        return {
            'seconds': td.total_seconds(),  # Rappresenta come secondi totali
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
        raise NotImplementedError("Missing implementation for datetime serialization")

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

    def _ast_to_obj(self, data: object) -> object:
        """Seleziona la conversione appropriata in base al $type"""

        # Gestione tipi primitivi
        if data is None or isinstance(data, (bool, int, float, str)):
            return data
        if isinstance(data, list):
            return [self._ast_to_obj(item) for item in data]

        # Gestione dizionari con $type
        if isinstance(data, dict):
            if '$type' not in data:
                # Dizionario semplice senza tipo
                return {k: self._ast_to_obj(v) for k, v in data.items()}

            type_name = data['$type']

            if type_name == 'User':
                return self._ast_to_user(data)
            elif type_name == 'Role':
                return self._ast_to_role(data)
            elif type_name == 'Credentials':
                return self._ast_to_credentials(data)
            elif type_name == 'Token':
                return self._ast_to_token(data)
            elif type_name == 'timedelta':
                return self._ast_to_timedelta(data)
            elif type_name == 'Request':
                return self._ast_to_request(data)
            elif type_name == 'Response':
                return self._ast_to_response(data)
            else:
                raise ValueError(f'Unknown type: {type_name}')

        raise ValueError(f'Cannot deserialize: {data}')

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
            expiration=datetime.fromisoformat(data['expiration']),
        )

    def _ast_to_timedelta(self, data: dict) -> timedelta:
        """Rebuilds timedelta from AST"""
        return timedelta(seconds=data['seconds'])

    def _ast_to_datetime(self, data):
        raise NotImplementedError("Missing implementation for datetime deserialization")

    def _ast_to_role(self, data):
        return Role[self._ast_to_obj(data['name'])]

    def _ast_to_request(self, data):
        return Request(
            name=self._ast_to_obj(data['name']),
            args=tuple(self._ast_to_obj(arg) for arg in data['args']),
            metadata=self._ast_to_obj(data.get('metadata')),
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
    from datetime import datetime, timedelta

    # Test originale con Request
    request = Request(
        name='my_function',
        args=(
            gc_credentials_wrong,
            gc_user,
            ["a string", 42, 3.14, True, False],
            {'key': 'value'},
            Response(None, 'an error'),
        )
    )
    serialized = serialize(request)
    print("Serialized Request", "=", serialized)
    deserialized = deserialize(serialized)
    print("Deserialized Request", "=", deserialized)
    assert request == deserialized

    # Test Token (con datetime in expiration)
    token = Token(
        user=gc_user,
        expiration=datetime.now() + timedelta(hours=1),
        signature="abc123signature"
    )
    serialized_token = serialize(token)
    print("\nSerialized Token", "=", serialized_token)
    deserialized_token = deserialize(serialized_token)
    print("Deserialized Token", "=", deserialized_token)
    print("Token expiration type:", type(deserialized_token.expiration))
    assert isinstance(deserialized_token.expiration, datetime)

    # Test timedelta (parametro duration per authenticate)
    duration = timedelta(hours=2, minutes=30)
    serialized_td = serialize(duration)
    print("\nSerialized timedelta", "=", serialized_td)
    deserialized_td = deserialize(serialized_td)
    print("Deserialized timedelta", "=", deserialized_td)
    assert duration == deserialized_td

    # Test Request simulate authenticate call
    auth_request = Request(
        name='authenticate',
        args=(gc_credentials_wrong, timedelta(hours=1))
    )
    serialized_auth = serialize(auth_request)
    print("\nSerialized auth Request", "=", serialized_auth)
    deserialized_auth = deserialize(serialized_auth)
    print("Deserialized auth Request", "=", deserialized_auth)
    assert auth_request == deserialized_auth

    print("\nAll tests passed.")