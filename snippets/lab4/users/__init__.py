from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol
import json
import base64

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
    username: str #This is not an User object anymore because it's not serializable. Usernames are assumed to be unique in a real-world scenario
    expiration: datetime
    signature: str

    def __post_init__(self):
        if not isinstance(self.username, str):
            raise ValueError(f"Expected object of type {str.__name__}, got: {self.username}")
        if not isinstance(self.expiration, datetime):
            raise ValueError(f"Expected object of type {datetime.__name__}, got: {self.expiration}")
        if not self.signature:
            raise ValueError("Signature is required")
        
    def __hash__(self):
        return super().__hash__(self.user, self.expiration, self.signature)
        
    def to_string(self) -> str:
        payload = {
            "username": self.username,
            "exp": self.expiration.isoformat(),
            "sig": self.signature,
        }
        json_bytes = json.dumps(payload).encode()
        return base64.urlsafe_b64encode(json_bytes).decode()

    @classmethod
    def from_string(cls, token_str: str) -> "Token":
        json_bytes = base64.urlsafe_b64decode(token_str.encode())
        payload = json.loads(json_bytes)

        return cls(
            username=payload["username"],
            expiration=datetime.fromisoformat(payload["exp"]),
            signature=payload["sig"],
        )    

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
