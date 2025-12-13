from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol, Optional, TypeVar

# ===============================
# Роли пользователя
# ===============================
class Role(Enum):
    ADMIN = 1
    USER = 2

# ===============================
# Базовый класс для копирования
# ===============================
_DataclassT = TypeVar("_DataclassT", bound="Datum")

@dataclass
class Datum:
    def copy(self: _DataclassT, **kwargs) -> _DataclassT:
        return replace(self, **kwargs)

# ===============================
# Пользователь
# ===============================
@dataclass
class User(Datum):
    username: str
    emails: set[str]
    full_name: Optional[str] = None
    role: Role = Role.USER
    password: Optional[str] = None

    def __post_init__(self):
        self.emails = set(self.emails)
        if not self.username:
            raise ValueError("Username is required")
        if not self.emails:
            raise ValueError("Email address is required")
        if self.role is None:
            self.role = Role.USER
    def to_dict(self):
        return {
            "username": self.username,
            "emails": list(self.emails),
            "full_name": self.full_name,
            "role": self.role.name,
        }
    
    @property
    def ids(self) -> set[str]:
        return {self.username} | self.emails

# ===============================
# Credentials
# ===============================
@dataclass
class Credentials(Datum):
    id: str
    password: str

    def __post_init__(self):
        if not self.id:
            raise ValueError("ID is required")
        if not self.password:
            raise ValueError("Password is required")

# ===============================
# Token
# ===============================
@dataclass
class Token(Datum):
    user: User
    expiration: datetime
    signature: str

    def __post_init__(self):
        if not isinstance(self.user, User):
            raise ValueError(f"Expected object of type User, got: {self.user}")
        if not isinstance(self.expiration, datetime):
            raise ValueError(f"Expected object of type datetime, got: {self.expiration}")
        if not self.signature:
            raise ValueError("Signature is required")
    def to_dict(self):
        return {
            "user": self.user.to_dict(),
            "expiration": self.expiration.isoformat(),
            "signature": self.signature,
        }
# ===============================
# Протоколы (интерфейсы)
# ===============================
class UserDatabase(Protocol):
    def add_user(self, user: User):
        ...

    def get_user(self, id: str) -> User:
        ...

    def check_password(self, credentials: Credentials) -> bool:
        ...

class AuthenticationService(Protocol):
    def authenticate(self, credentials: Credentials, duration: Optional[timedelta] = None) -> Token:
        ...

    def validate_token(self, token: Token) -> bool:
        ...
