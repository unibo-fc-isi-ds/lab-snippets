from .users import User, Credentials, Token, Role
from datetime import datetime
import json
from dataclasses import dataclass


@dataclass
class Request:
    name: str
    args: tuple

    def __post_init__(self):
        self.args = tuple(self.args)


@dataclass
class Response:
    result: object | None
    error: str | None


class Serializer:
    def serialize(self, obj):
        return self._dict_to_string(self._to_dict(obj))
    
    def _dict_to_string(self, data):
        return json.dumps(data, indent=2)

    def _to_dict(self, obj):
        method_name = f'_{type(obj).__name__.lower()}_to_dict'
        if hasattr(self, method_name):
            data = getattr(self, method_name)(obj)
            data['$type'] = type(obj).__name__
            return data
        raise ValueError(f"Unsupported type {type(obj)}")
    
    def _user_to_dict(self, user: User):
        return {
            'username': user.username,
            'emails': list(user.emails),
            'full_name': user.full_name,
            'role': self._role_to_dict(user.role),
            'password': user.password,
        }
    
    def _credentials_to_dict(self, credentials: Credentials):
        return {
            'id': credentials.id,
            'password': credentials.password,
        }
    
    def _token_to_dict(self, token: Token):
        return {
            'signature': token.signature,
            'user': self._to_dict(token.user),
            'expiration': token.expiration.isoformat(),
        }
    
    def _role_to_dict(self, role: Role):
        return {
            'name': role.name,
        }
    
    def _request_to_dict(self, request: Request):
        return {
            'name': request.name,
            'args': [self._to_dict(arg) for arg in request.args],
        }
    
    def _response_to_dict(self, response: Response):
        return {
            'result': self._to_dict(response.result) if response.result is not None else None,
            'error': response.error,
        }


class Deserializer:
    def deserialize(self, string):
        return self._dict_to_obj(json.loads(string))
    
    def _dict_to_obj(self, data):
        method_name = f'_dict_to_{data["$type"].lower()}'
        if hasattr(self, method_name):
            return getattr(self, method_name)(data)
        raise ValueError(f"Unsupported type {data['type']}")
    
    def _dict_to_user(self, data):
        return User(
            username=data['username'],
            emails=set(data['emails']),
            full_name=data['full_name'],
            role=self._dict_to_role(data['role']),
            password=data['password'],
        )
    
    def _dict_to_credentials(self, data):
        return Credentials(
            id=data['id'],
            password=data['password'],
        )
    
    def _dict_to_token(self, data):
        return Token(
            signature=data['signature'],
            user=self._dict_to_obj(data['user']),
            expiration=datetime.fromisoformat(data['expiration']),
        )
    
    def _dict_to_role(self, data):
        return Role[data['name']]
    
    def _dict_to_request(self, data):
        return Request(
            name=data['name'],
            args=tuple(self._dict_to_obj(arg) for arg in data['args']),
        )
    
    def _dict_to_response(self, data):
        return Response(
            result=self._dict_to_obj(data['result']) if data['result'] is not None else None,
            error=data['error'],
        )


DEFAULT_SERIALIZER = Serializer()
DEFAULT_DESERIALIZER = Deserializer()


def serialize(obj):
    return DEFAULT_SERIALIZER.serialize(obj)


def deserialize(string):
    return DEFAULT_DESERIALIZER.deserialize(string)


if __name__ == '__main__':
    token = Token(
        signature='signature',
        user=User(
            username='username',
            emails={'email1', 'email2'},
            full_name='full_name',
            role=Role.ADMIN,
            password='password',
        ),
        expiration=datetime(2021, 1, 1),
    )
    serialized = serialize(token)
    print(serialized)
    deserialized = deserialize(serialized)
    print(deserialized)
    assert token == deserialized