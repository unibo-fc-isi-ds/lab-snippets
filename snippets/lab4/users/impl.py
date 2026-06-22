from ..users import *
from ..example1_presentation import serialize, deserialize
import hashlib
import os
from datetime import datetime

PATH_FILE = os.path.abspath(__file__)
PATH_FOLDER = os.path.dirname(PATH_FILE)

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
            result = Token(user, expiration, signature)
            self._log(f"Generate token for user {credentials.id}: {result}")
            return result
        raise ValueError("Invalid credentials")
    
    def __validate_token_signature(self, token: Token) -> bool:
        return token.signature == _compute_sha256_hash(f"{token.user}{token.expiration}{self.__secret}")

    def validate_token(self, token: Token) -> bool:
        result = token.expiration > datetime.now() and self.__validate_token_signature(token)
        self._log(f"{token} is " + ('valid' if result else 'invalid'))
        return result
    
def load_tokens_from_file(): #loads the existing tokens from the file
    try:
        with open(os.path.join(PATH_FOLDER, 'tokens.json'), 'r') as f:
            content = f.read()
            if content:
                return deserialize(content)
            return {}
    except FileNotFoundError:
        return {}
    except Exception as e:
        print(f"Error loading existing tokens: {e}")
        return {}

def save_token_to_file(new_token): #adding a new token to the file
    try:
        existing_tokens = load_tokens_from_file()
        token_id = new_token.signature
        existing_tokens[token_id] = new_token
        with open(os.path.join(PATH_FOLDER, 'tokens.json'), 'w') as f:
            f.write(serialize(existing_tokens))     
    except AttributeError:
        print("The token does not have a signature attribute required for the key")
    except Exception as e:
        print(f"An error occurred while saving the token: {e}")

def remove_tokens_in_file(): #removes all the tokens
    tokens = {}
    with open(os.path.join(PATH_FOLDER, 'tokens.json'), 'w') as f:
        f.write(serialize(tokens))    
