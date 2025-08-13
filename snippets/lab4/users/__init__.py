from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol


# un Enum per specificare il ruolo dei membri del sistema RPC
class Role(Enum):
    ADMIN = 1
    USER = 2

# una classe che stabilisce come i dati di una classe possano essere sostituiti da nuovi argomenti passati
class Datum:
    def copy(self, **kwargs):
        return replace(self, **kwargs)


# grazie al decoratore @dataclass, vengono aggiunti a User diversi metodi quali init, la possibilità di avere dei campi
# che verranno poi riempiti durante init,
@dataclass
class User(Datum):
    username: str
    emails: set[str]
    full_name: str | None = None
    role: Role = Role.USER
    password: str | None = None

    # un meotodo che viene chiamato subito dopo la init, che controlla se siano stati passati mail e username
    def __post_init__(self):
        self.emails = set(self.emails)
        if self.role is None:
            self.role = Role.USER
        if not self.username:
            raise ValueError("Username is required")
        if not self.emails:
            raise ValueError("Email address is required")   

    # un getter per recuperare id dello User
    @property
    def ids(self):
        return {self.username} | self.emails


# un altra classe con decoratore che ha come campi id e password
@dataclass
class Credentials(Datum):
    id: str
    password: str

    # anche qui abbiamo un metodo che viene istantaneamente chiamato dopo __init__ per verificare che siano stati inseriti id e password
    def __post_init__(self):
        if not self.id:
            raise ValueError("ID is required")
        if not self.password:
            raise ValueError("Password is required")


# ulteriore dataclass con campi user, data in cui il token morirà e una firma
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
    

# una classe particolare di tipo "Protocol". Funziona in una maniera similare ad un'Interfaccia di Java, dove definisco
# i metodi con i parametri e valori di ritorno, che verranno poi implementati da altre classi
class UserDatabase(Protocol):
    def add_user(self, user: User):
        ...
    
    def get_user(self, id: str) -> User:
        ...
    
    def check_password(self, credentials: Credentials) -> bool:
        ...


# classe che funge da interfaccia per sistemi di Autenticazione, altre classi implementeranno i metodi indicati
class AuthenticationService(Protocol):
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        ...

    def validate_token(self, token: Token) -> bool:
        ...
