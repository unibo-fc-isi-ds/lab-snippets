from ..users import *
import hashlib

# una funzione hash usata per le password
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


# questa è la classe che implementa l'interfaccia UserDatabase
class InMemoryUserDatabase(UserDatabase, _Debuggable):
    def __init__(self, debug: bool = True):
        _Debuggable.__init__(self, debug)
        self.__users: dict[str, User] = {} # creo qui il database che sarà un dizionario dove ogni chiave ID corrisponde un utente
        self._log("User database initialized with empty users")
    
    # metodo per aggiungere gli users
    def add_user(self, user: User):
        # controllo prima di tutto se questo user con questo ID non sia già stato inserito
        for id in user.ids:
            if id in self.__users:
                raise ValueError(f"User with ID {id} already exists")
        # verifico poi che l'utente abbia inserito una sua password, altrimenti segnalo errore
        if user.password is None:
            raise ValueError("Password digest is required")
        user = user.copy(password=_compute_sha256_hash(user.password)) # sostituisco la password con la versione hashata
        for id in user.ids:
            self.__users[id] = user # aggiungo poi al dizionario il nuovo user specificando come chiave il suo ID
        self._log(f"Add: {user}")

    # un semplice metodo che restitiusce uno user con un certo id
    def __get_user(self, id: str) -> User:
        if id not in self.__users:
            raise KeyError(f"User with ID {id} not found")
        return self.__users[id]
    
    def get_user(self, id: str) -> User:
        result = self.__get_user(id).copy(password=None)
        self._log(f"Get user with ID {id}: {result}")
        return result

    # un metodo per verificare la password
    def check_password(self, credentials: Credentials) -> bool:
        try:
            user = self.__get_user(credentials.id) # recupero lo user usando l'ID delle credenziali e poi verifico se
            # la password hashata salvata sia uguale a quella indicata dalle credenziali passate
            result = user.password == _compute_sha256_hash(credentials.password)
        except KeyError:
            result = False
        # segnalo qui se è andato tutto correttamente o se ci sono stati problemi
        self._log(f"Checking {credentials}: {'correct' if result else 'incorrect'}")
        return result
    

# questa è la classe che implementa l'interfaccia AuthenticationService
class InMemoryAuthenticationService(AuthenticationService, _Debuggable):
    def __init__(self, database: UserDatabase, secret: str = None, debug: bool = True):
        _Debuggable.__init__(self, debug)
        # riceve in ingresso uno UserDatabase per svolgere il compito di autenticazione
        # se non riceve un secret, lo crea lui personalmente
        self.__database = database
        if not secret:
            import uuid
            secret = str(uuid.uuid4())
        self.__secret = secret
        self._log(f"Authentication service initialized with secret {secret}")
    
    # questo metodo serve per restituire un token di autenticazione
    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        # stabilisco la durata (creandone una o prendendo quella passata in ingresso)
        if duration is None:
            duration = timedelta(days=1)
        # eseguo poi un controllo della password, verificando che si stia autenticando l'utente corretto
        if self.__database.check_password(credentials):
            # se è tutto ok, creo la data di scadenza del token, recupero l'utente dal database in base alle credenziali
            expiration = datetime.now() + duration
            user = self.__database.get_user(credentials.id)
            # stabilisco poi qui una firma, che sarà il risultato hash di una stringa composta da utente, data scadenza e segreto
            signature = _compute_sha256_hash(f"{user}{expiration}{self.__secret}")
            # questi 3 elementi li uso per creare il Token che restituisco
            result = Token(user, expiration, signature)
            self._log(f"Generate token for user {credentials.id}: {result}")
            return result
        raise ValueError("Invalid credentials")
    
    # con questo metodo, verifico che la firma del token di autenticazione sia quella corretta
    def __validate_token_signature(self, token: Token) -> bool:
        return token.signature == _compute_sha256_hash(f"{token.user}{token.expiration}{self.__secret}")

    # infine, verifico che il token sia valido, ovvero verifico che non il token non sia scaduto e che la firma sia corretta
    # segnalando se necessario errore
    def validate_token(self, token: Token) -> bool:
        result = token.expiration > datetime.now() and self.__validate_token_signature(token)
        self._log(f"{token} is " + ('valid' if result else 'invalid'))
        return result
