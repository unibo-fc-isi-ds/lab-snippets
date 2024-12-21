from snippets.lab4.example1_presentation import TYPE_AUTH, deserialize, serialize
from snippets.lab4.example3_rpc_client import ClientStub
from ..users import *
import hashlib


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
        self._log(f"Add: {user}")

    def __get_user(self, id: str) -> User:
        if id not in self.__users:
            raise KeyError(f"User with ID {id} not found")
        return self.__users[id]
    
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

class RemoteAuthenticationService(ClientStub, AuthenticationService):
    def __init__(self, server_address):
        super().__init__(server_address)
    
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        return self.rpc('authenticate', TYPE_AUTH, credentials, duration)
    
    def validate_token(self, token: Token) -> bool:
        return self.rpc('validate_token', TYPE_AUTH, token)
    
    def check_privileges(self, db: UserDatabase, credentials: Credentials, token: Token) -> bool:
        if not db.check_password(credentials):
            raise ValueError("Invalid credentials")

        if not self.validate_token(token):
            raise ValueError("Invalid token")
                
        if token.user.role != Role.ADMIN:
            raise ValueError("Insufficient privileges")
    

TOKENS_DIR = 'tokens'

class TokenStorage():
    def __init__(self, directory: str = TOKENS_DIR):
        self.__directory = directory
        import os
        os.makedirs(directory, exist_ok=True)
    
    def store(self, token: Token):
        with open(f"{self.__directory}/{token.user.username}.json", 'w') as file:
            serialized = serialize(token)
            file.write(serialized)
    
    def load(self, username: str) -> Token:
        with open(f"{self.__directory}/{username}.json", 'r') as file:
            return deserialize(file.read())
    
    def remove(self, id: str):
        import os
        os.remove(f"{self.__directory}/{id}.json")
    
    def __contains__(self, id: str) -> bool:
        import os
        return os.path.isfile(f"{self.__directory}/{id}.token")