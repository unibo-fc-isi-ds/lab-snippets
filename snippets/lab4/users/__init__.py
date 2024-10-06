from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol


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
    role: Role = Role.USER
    password: str | None = None

    def __post_init__(self):
        self.emails = set(self.emails)
        if self.role is None:
            self.role = Role.USER
        if not self.username:
            raise ValueError("Username is required")
        if not self.emails:
            raise ValueError("Email address is required")   

    @property
    def ids(self):
        return {self.username} | self.emails


@dataclass
class Credentials(Datum):
    id: str
    password: str

    def __post_init__(self):
        if not self.id:
            raise ValueError("ID is required")
        if not self.password:
            raise ValueError("Password is required")


@dataclass
class Token(Datum):
    user: User
    expiration: datetime
    signature: str

    def __post_init__(self):
        if not isinstance(self.user, User):
            raise ValueError(f"Expected object of type {User.__name__}, got: {self.user}")
        if not isinstance(self.expiration, datetime):
            raise ValueError(f"Expected object of type {datetime.__name__}, got: {self.expiration}")
        if not self.signature:
            raise ValueError("Signature is required")
    

class UserDatabase(Protocol):
    def add_user(self, user: User):
        ...
    
    def get_user(self, id: str) -> User:
        ...
    
    def check_password(self, credentials: Credentials) -> bool:
        ...


class AuthenticationService(Protocol):
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        ...

    def validate_token(self, token: Token) -> bool:
        ...
