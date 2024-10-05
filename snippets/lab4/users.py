from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
import hashlib


def compute_sha256_hash(input: str) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(input.encode('utf-8'))
    return sha256_hash.hexdigest()


class Role(Enum):
    ADMIN = 1
    USER = 2


class Datum:
    def copy(self, **kwargs):
        return replace(self, **kwargs)


@dataclass
class User(Datum):
    username: str
    emails: set[str]
    full_name: str | None = None
    role: str = Role.USER
    password: str | None = None

    def __post_init__(self):
        self.emails = set(self.emails)

    @property
    def ids(self):
        return {self.username} | self.emails


@dataclass
class Credentials(Datum):
    id: str
    password: str


@dataclass
class Token(Datum):
    signature: str
    user: User
    expiration: datetime


class UserDatabase:
    def __init__(self):
        self.__users = {}
    
    def add_user(self, user: User):
        for id in user.ids:
            if id in self.__users:
                raise ValueError(f"User with {id} already exists")
        if user.password is None:
            raise ValueError("Password digest is required")
        user = user.copy(password=compute_sha256_hash(user.password))
        for id in user.ids:
            self.__users[id] = user

    def __get_user(self, id: str) -> User:
        if id not in self.__users:
            raise KeyError(f"User with {id} not found")
        return self.__users[id]
    
    def get_user(self, id: str) -> User:
        return self.__get_user(id).copy(password=None)

    def check_password(self, credentials: Credentials) -> bool:
        user = self.__get_user(credentials.id)
        return user.password == compute_sha256_hash(credentials.password)
    

class AuthenticationService:
    def __init__(self, database: UserDatabase, secret: str = None):
        self.__database = database
        if not secret:
            import uuid
            secret = str(uuid.uuid4())
        self.__secret = secret
    
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        if duration is None:
            duration = timedelta(days=1)
        if self.__database.check_password(credentials):
            expiration = datetime.now() + duration
            user = self.__database.get_user(credentials.id)
            signature = compute_sha256_hash(f"{user}{expiration}{self.__secret}")
            return Token(signature, user, expiration)
    
    def __validate_token_signature(self, token: Token) -> bool:
        return token.signature == compute_sha256_hash(f"{token.user}{token.expiration}{self.__secret}")

    def validate_token(self, token: Token) -> bool:
        return token.expiration > datetime.now() and self.__validate_token_signature(token)
