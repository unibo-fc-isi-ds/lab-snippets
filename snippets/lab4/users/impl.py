from ..users import *
import hashlib

#Funzione per calcolare l'hash SHA-256 di una stringa
def _compute_sha256_hash(input: str) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(input.encode('utf-8'))
    return sha256_hash.hexdigest()

#Classe di supporto per il debug --> logga le operazioni se il debug è attivo
class _Debuggable:
    def __init__(self, debug: bool = True):
        self.__debug = debug
    
    def _log(self, *args, **kwargs): #Metodo per stampare i log se il debug è attivo
        if self.__debug:
            print(*args, **kwargs)

#Implementazione in memoria di UserDatabase
class InMemoryUserDatabase(UserDatabase, _Debuggable):
    def __init__(self, debug: bool = True):
        _Debuggable.__init__(self, debug) #Inizializza la parte di debug
        self.__users: dict[str, User] = {} #Dizionario per memorizzare gli utenti
        self._log("User database initialized with empty users")
    
    #implementazione del metodo add_user dell'interfaccia UserDatabase
    def add_user(self, user: User):
        for id in user.ids:
            if id in self.__users: #se l'id esiste già
                raise ValueError(f"User with ID {id} already exists")
        if user.password is None: #se la password è None
            raise ValueError("Password digest is required")
        user = user.copy(password=_compute_sha256_hash(user.password)) 
        #Crea una copia dell'utente con la password hashata
        for id in user.ids:
            self.__users[id] = user #aggiunge l'utente al dizionario per ogni suo id
        self._log(f"Add: {user}")

    #Metodo privato per ottenere un utente dato un id
    def __get_user(self, id: str) -> User:
        if id not in self.__users:
            raise KeyError(f"User with ID {id} not found")
        return self.__users[id]
    
    #implementazione del metodo get_user dell'interfaccia UserDatabase
    def get_user(self, id: str) -> User:
        result = self.__get_user(id).copy(password=None)
        self._log(f"Get user with ID {id}: {result}")
        return result

    #implementazione del metodo check_password dell'interfaccia UserDatabase
    def check_password(self, credentials: Credentials) -> bool:
        try:
            user = self.__get_user(credentials.id)
            result = user.password == _compute_sha256_hash(credentials.password) #confronta l'hash della password
        except KeyError: #se l'utente non esiste
            result = False
        self._log(f"Checking {credentials}: {'correct' if result else 'incorrect'}")
        return result
    
#Implementazione in memoria di AuthenticationService
class InMemoryAuthenticationService(AuthenticationService, _Debuggable):
    def __init__(self, database: UserDatabase, secret: str = None, debug: bool = True):
        _Debuggable.__init__(self, debug) #Inizializza la parte di debug
        self.__database = database #Database degli utenti
        if not secret: #se non è stato fornito un secret --> chiave segreta per criptare i token
            import uuid #importa il modulo uuid per generare un identificatore unico
            secret = str(uuid.uuid4()) #genera un uuid e lo converte in stringa
        self.__secret = secret
        self._log(f"Authentication service initialized with secret {secret}")
    
    #Implementazione del metodo authenticate dell'interfaccia AuthenticationService
    #Autentica un utente e genera un token
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token: #restituisce un Token
        if duration is None: #se non è stata fornita una durata
            duration = timedelta(days=1) #imposta la durata di default a 1 giorno
        if self.__database.check_password(credentials): #se le credenziali sono corrette
            expiration = datetime.now() + duration #calcola la data di scadenza del token
            user = self.__database.get_user(credentials.id) #ottiene l'utente dal database
            signature = _compute_sha256_hash(f"{user}{expiration}{self.__secret}") #calcola la firma del token --> hash di user, expiration e secret
            result = Token(user, expiration, signature) #crea il token
            self._log(f"Generate token for user {credentials.id}: {result}")
            return result
        raise ValueError("Invalid credentials") #se le credenziali sono errate
    
    #Metodo privato per validare la firma del token
    def __validate_token_signature(self, token: Token) -> bool:
        return token.signature == _compute_sha256_hash(f"{token.user}{token.expiration}{self.__secret}")

    #Implementazione del metodo validate_token dell'interfaccia AuthenticationService
    #Valida un token
    def validate_token(self, token: Token) -> bool:
        result = token.expiration > datetime.now() and self.__validate_token_signature(token)
        #Se il token non è scaduto e la firma è valida --> è ancora valido
        self._log(f"{token} is " + ('valid' if result else 'invalid'))
        return result
