from doctest import FAIL_FAST
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
    def __init__(self, debug: bool = False):
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
    def get_user_role(self, id: str) -> Role:
        user = self.__get_user(id)
        return user.role

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

    def check_permission(self, token: Token, required_role: Role):
        if not self.validate_token(token):
            raise ValueError("Invalid or expired token")
        if token.user.role != required_role:
            raise ValueError(f"Access denied: {required_role} role required")
        self._log(f"User {token.user.username} has sufficient permissions")
