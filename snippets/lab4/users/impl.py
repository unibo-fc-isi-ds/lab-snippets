from snippets.lab4.example1_presentation import Serializer, Deserializer
from ..users import *
import hashlib
import os


def _compute_sha256_hash(input: str) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(input.encode('utf-8'))
    return sha256_hash.hexdigest()


class _Debuggable:
    def __init__(self, debug: bool = True):
        self.__debug = debug
    
    def _log(self, *args, **kwargs):
        if self.__debug:
            print(*args, **kwargs)


class InMemoryUserDatabase(UserDatabase, _Debuggable):
    def __init__(self, debug: bool = True):
        _Debuggable.__init__(self, debug)
        self.__DATABASE_FILE = './snippets/lab4/database.json'

        users = self.__read_users_from_file()
        if users:
            self.__users: dict[str, User] = users
            self._log("User database initialized with existing users")
        else:
            self.__users: dict[str, User] = {}
            self._log("User database initialized with empty users")
    
    def add_user(self, user: User):
        for id in user.ids:
            if id in self.__users:
                raise ValueError(f"User with ID {id} already exists")
        if user.password is None:
            raise ValueError("Password digest is required")
        user = user.copy(password=_compute_sha256_hash(user.password))
        for id in user.ids:
            self.__users[id] = user
        self.__store_users_to_file()
        self._log(f"Add: {user}")
    
    def get_user(self, id: str) -> User:
        result = self.__get_user(id).copy(password=None)
        self._log(f"Get user with ID {id}: {result}")
        return result

    def check_password(self, credentials: Credentials) -> bool:
        try:
            user = self.__get_user(credentials.id)
            result = user.password == _compute_sha256_hash(credentials.password)
        except KeyError:
            result = False
        self._log(f"Checking {credentials}: {'correct' if result else 'incorrect'}")
        return result
    
    def __get_user(self, id: str) -> User:
        if id not in self.__users:
            raise KeyError(f"User with ID {id} not found")
        return self.__users[id]
    
    def __store_users_to_file(self) -> None:
        with open(self.__DATABASE_FILE, 'w') as f:
            serializer = Serializer()
            f.write(serializer.serialize(self.__users))

    def __read_users_from_file(self) -> dict[str, User]:
        if not os.path.exists(self.__DATABASE_FILE):
            return {}
        with open(self.__DATABASE_FILE, 'r') as f:
            deserializer = Deserializer()
            return deserializer.deserialize(f.read())
    

class InMemoryAuthenticationService(AuthenticationService, _Debuggable):
    def __init__(self, database: UserDatabase, secret: str = None, debug: bool = True):
        _Debuggable.__init__(self, debug)
        self.__database = database
        if not secret:
            import uuid
            secret = str(uuid.uuid4())
        self.__secret = secret
        self._log(f"Authentication service initialized with secret {secret}")
    
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        if duration is None:
            duration = timedelta(days=1)
        if self.__database.check_password(credentials):
            expiration = datetime.now() + duration
            user = self.__database.get_user(credentials.id)
            signature = _compute_sha256_hash(f"{user}{expiration}{self.__secret}")
            result = Token(user, expiration, signature)
            self._log(f"Generate token for user {credentials.id}: {result}")
            return result
        raise ValueError("Invalid credentials")
    
    def __validate_token_signature(self, token: Token) -> bool:
        return token.signature == _compute_sha256_hash(f"{token.user}{token.expiration}{self.__secret}")

    def validate_token(self, token: Token) -> bool:
        result = token.expiration > datetime.now() and self.__validate_token_signature(token)
        self._log(f"{token} is " + ('valid' if result else 'invalid'))
        return result
