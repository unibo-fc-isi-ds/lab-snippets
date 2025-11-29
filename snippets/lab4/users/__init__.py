from dataclasses import dataclass, replace
from datetime import datetime, timedelta
from enum import Enum
from typing import Protocol

#Contiene la lista delle classi e interfacce principali per la gestione degli utenti e dell'autenticazione

#Enumerativo dei ruoli utente
class Role(Enum):
    ADMIN = 1
    USER = 2

#Base comune per le dataclass
class Datum:
    def copy(self, **kwargs):
        return replace(self, **kwargs)
# crea una nuova istanza della dataclass,
# copiando tutti i campi dall’istanza originale e sostituendo quelli passati come keyword argument.

@dataclass # --> Decoratore che indica a python che questa classe serve sopratutto per immagazzinare dati
class User(Datum): #Classe che rappresenta un utente
    username: str 
    emails: set[str] #set di stringhe --> collezione non ordinata di elementi unici
    full_name: str | None = None #stringa o None, di default None
    role: Role = Role.USER #Ruolo di default USER
    password: str | None = None #stringa o None, di default None

    #Metodo chiamato automaticamente dopo l'inizializzazione dell'istanza
    def __post_init__(self):
        self.emails = set(self.emails) #Assicura che emails sia un set
        if self.role is None:
            self.role = Role.USER
        if not self.username:
            raise ValueError("Username is required")
        if not self.emails:
            raise ValueError("Email address is required")   

    @property # --> Decoratore possiamo accedere a questo metodo come se fosse un attributo
    def ids(self):
        return {self.username} | self.emails 
    # {self.username} crea un set con l'username
    # self.emails è già un set di email
    # | è l'operatore di unione per i set, quindi restituisce un set che contiene sia l'username che tutte le email

@dataclass
class Credentials(Datum): #Classe che rappresenta le credenziali di un utente
    id: str
    password: str

    def __post_init__(self):
        if not self.id: #Se l'id è vuoto
            raise ValueError("ID is required")
        if not self.password:
            raise ValueError("Password is required")


@dataclass
class Token(Datum): #Classe che rappresenta un token di autenticazione
    user: User
    expiration: datetime
    signature: str

    def __post_init__(self):
        if not isinstance(self.user, User): #se user non è un'istanza di User
            raise ValueError(f"Expected object of type {User.__name__}, got: {self.user}")
        if not isinstance(self.expiration, datetime): #se expiration non è un'istanza di datetime
            raise ValueError(f"Expected object of type {datetime.__name__}, got: {self.expiration}")
        if not self.signature: #se signature è vuota
            raise ValueError("Signature is required")
    

class UserDatabase(Protocol):
    def add_user(self, user: User): #metodo per aggiungere un utente
        ... #non c'è implementazione, solo la firma del metodo
    
    def get_user(self, id: str) -> User: #metodo per ottenere un utente dato un id
        ...
    
    def check_password(self, credentials: Credentials) -> bool: #metodo per controllare le credenziali
        ...


class AuthenticationService(Protocol):
    #Metodo per autenticare un utente dato le credenziali
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        ...

    #Metodo per verificare la validità di un token
    def validate_token(self, token: Token) -> bool:
        ...
