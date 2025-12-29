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
    def __init__(self, debug: bool = True):
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

    def check_password(self, credentials: Credentials) -> bool:
        try:
            user = self.__get_user(credentials.id)
            result = user.password == _compute_sha256_hash(credentials.password)
        except KeyError:
            result = False
        self._log(f"Checking {credentials}: {'correct' if result else 'incorrect'}")
        return result
    

class InMemoryAuthenticationService(AuthenticationService, _Debuggable):
    # These two lists are used to keep track of authenticated users and tokens. They are redundant but allow O(1) lookups in both ways, allowing fast access even with thousands of users.
    authenticated_users_to_tokens = {}
    authenticated_tokens_to_users = {}
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
            result = Token(user.username, expiration, signature)
            self._log(f"Generate token for user {credentials.id}: {result}")
            self.authenticated_users_to_tokens[credentials.id] = result.signature
            self.authenticated_tokens_to_users[result.signature] = credentials.id
            return result
        raise ValueError("Invalid credentials")
    
    def __validate_token_signature(self, token: Token) -> bool:
        return token.signature == _compute_sha256_hash(f"{token.username}{token.expiration}{self.__secret}")

    def validate_token(self, token: Token) -> bool:
        result = token.expiration > datetime.now() and self.__validate_token_signature(token)
        self._log(f"{token} is " + ('valid' if result else 'invalid'))
        return result
    
    def is_authenticated(self, tokenSignature:str = None, token: Token = None) -> bool:
        if token is not None:
            print(f"is_authenticated with token({token}): {token.signature in self.authenticated_users_to_tokens.values()}")
            return token.signature in self.authenticated_users_to_tokens.values() #and self.validate_token(token)
        else:
            print(f"is_authenticated with signatureToken({tokenSignature}): {tokenSignature in self.authenticated_users_to_tokens.values()}")
            return tokenSignature in self.authenticated_users_to_tokens.values() #and self.validate_token(Token.from_string(signatureToken))
    #Access is granted if the user is authenticated, the read target is itself, or the user is an admin
    def grant_read_access(self, userid_to_access: str, signatureToken:str = None, token: Token = None) -> bool:
        print(f"grant_read_access({token}, {userid_to_access})")
        assert self.is_authenticated(token = token, tokenSignature = signatureToken)
        user_id = ""
        if token is not None:
            user_id = self.authenticated_tokens_to_users[token.signature]
        else:
            user_id = self.authenticated_tokens_to_users[signatureToken]
        if user_id == userid_to_access:
            print("User is self")
            return True
        if self.__database.get_user(user_id).role == Role.ADMIN:
            print("User is admin")
            return True
        print("Access denied")
        return False
    
class DatabaseWithAuthenticationService(_Debuggable):
    def __init__(self, database: UserDatabase, authentication_service: AuthenticationService, debug: bool = True):
        self.__database = database
        self.__authentication_service = authentication_service
        _Debuggable.__init__(self, debug)

    def authenticate(self, credentials: Credentials, duration: timedelta = None) -> Token:
        return self.__authentication_service.authenticate(credentials, duration)

    def add_user(self, user: User):
        self.__database.add_user(user)

    def get_user(self, id: str, token: Token = None, tokenSignature: str = None):
        print(f"get_user({id}, {token})")
        print(f"get_user({id}, {tokenSignature})")
        if self.__authentication_service.grant_read_access(id, tokenSignature, token):
            self._log(f"Get user with ID {id}: {self.__database.get_user(id)}")
            return self.__database.get_user(id)
        raise ValueError("Access denied")

    def check_password(self, credentials: Credentials):
        return self.__database.check_password(credentials)
        