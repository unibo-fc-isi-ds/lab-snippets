from dataclasses import dataclass, replace as defensive_copy
from datetime import datetime, timedelta
from enum import Enum
import hashlib


def compute_sha256_hash(input: str) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(input.encode('utf-8'))
    return sha256_hash.hexdigest()


class Role(Enum):
    ADMIN = 'admin'
    USER = 'user


@dataclass
class User:
    username: str
    email: str
    full_name: str | None = None
    role: str = Role.USER
    password: str | None = None

    @property
    def ids(self):
        return {self.username, self.email}

@dataclass
class Credentials:
    id: str
    password: str


@dataclass
class Token:
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
            raise ValueError("Password is required")
        user = defensive_copy(user, password=compute_sha256_hash(user.password))
        self.__users[user.username] = user
        self.__users[user.email] = user

    def __get_user(self, id: str) -> User:
        if id not in self.__users:
            raise KeyError(f"User with {id} not found")
        return self.__users[id]
    
    def get_user(self, id: str) -> User:
        return defensive_copy(self.__get_user(id), password=None)

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
