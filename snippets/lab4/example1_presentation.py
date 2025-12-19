from .users import User, Credentials, Token, Role
from datetime import datetime
import json
from dataclasses import dataclass

#Questo file definisce le classi e le funzioni per serializzare e deserializzare
#oggetti relativi al sistema di autenticazione e gestione utenti in formato JSON.

#Serializzazione --> {"$type": "Request", "name":"...", "args":[...]}
@dataclass
class Request: #Richiesta RPC

    service : str #nome del servizio (UserDatabase o AuthenticationService)
    name: str #nome del metodo da chiamare
    args: tuple #argomenti del metodo
    authentication_token : Token | None = None  #La richiesta prevede un autenticazione ?

    def __post_init__(self): #Converte args in tupla se non lo è già
        self.args = tuple(self.args)

#Deserializzazione --> {"$type": "Response", "result": {...}, "error": "..."}
@dataclass
class Response: #Risposta RPC

    result: object | None #risultato della chiamata
    error: str | None #messaggio di errore, None se non c'è errore

#Classe per Serializzare
class Serializer: # oggetto --> ast --> stringa
    primitive_types = (int, float, str, bool, type(None))
    container_types = (list)

    def serialize(self, obj):
        return self._ast_to_string(self._to_ast(obj))

    def _ast_to_string(self, data):
        return json.dumps(data, indent=2)

    def _to_ast(self, obj):
        if isinstance(obj, self.primitive_types):
            return obj
        if isinstance(obj, self.container_types):
            return [self._to_ast(item) for item in obj]
        if isinstance(obj, dict):
            return {key: self._to_ast(value) for key, value in obj.items()}
        # selects the appropriate method to convert the object to AST via reflection
        method_name = f'_{type(obj).__name__.lower()}_to_ast'
        if hasattr(self, method_name):
            data = getattr(self, method_name)(obj)
            data['$type'] = type(obj).__name__
            return data
        raise ValueError(f"Unsupported type {type(obj)}")

    # Metodi specifici per convertire ogni tipo di oggetto in AST (dictionary)

    def _user_to_ast(self, user: User): 
        return {
            'username': self._to_ast(user.username),
            'emails': [self._to_ast(email) for email in user.emails],
            'full_name': self._to_ast(user.full_name),
            'role': self._to_ast(user.role),
            'password': self._to_ast(user.password),
        }

    def _credentials_to_ast(self, credentials: Credentials):
        return {
            'id': self._to_ast(credentials.id),
            'password': self._to_ast(credentials.password),
        }

    def _token_to_ast(self, token: Token):
        return {
            'signature': self._to_ast(token.signature),
            'user': self._to_ast(token.user),
            'expiration': self._to_ast(token.expiration),
        }

    def _datetime_to_ast(self, dt: datetime):
        return { 'datetime': dt.isoformat() } # converte in stringa in ISO
    
    def _role_to_ast(self, role: Role):
        return {'name': role.name}

    def _request_to_ast(self, request: Request):
        return {
            'service': self._to_ast(request.service), #aggiunto 
            'name': self._to_ast(request.name),
            'args': [self._to_ast(arg) for arg in request.args],
            'authentication_token': self._to_ast(request.authentication_token) #aggiunto
        }

    def _response_to_ast(self, response: Response):
        return {
            'result': self._to_ast(response.result) if response.result is not None else None,
            'error': self._to_ast(response.error),
        }

#Classe per Deserializzare stringa --> ast --> oggetto
class Deserializer:
    def deserialize(self, string):
        return self._ast_to_obj(self._string_to_ast(string))

    def _string_to_ast(self, string):
        return json.loads(string)

    def _ast_to_obj(self, data):
        if isinstance(data, dict):
            if '$type' not in data:
                return {key: self._ast_to_obj(value) for key, value in data.items()}
            # selects the appropriate method to convert the AST to object via reflection
            method_name = f'_ast_to_{data["$type"].lower()}'
            if hasattr(self, method_name):
                return getattr(self, method_name)(data)
            raise ValueError(f"Unsupported type {data['type']}")
        if isinstance(data, list):
            return [self._ast_to_obj(item) for item in data]
        return data

    def _ast_to_user(self, data):
        return User(
            username=self._ast_to_obj(data['username']),
            emails=list(self._ast_to_obj(data['emails'])),
            full_name=self._ast_to_obj(data['full_name']),
            role=self._ast_to_obj(data['role']),
            password=self._ast_to_obj(data['password']),
        )

    def _ast_to_credentials(self, data):
        return Credentials(
            id=self._ast_to_obj(data['id']),
            password=self._ast_to_obj(data['password']),
        )

    def _ast_to_token(self, data):
        return Token(
            signature=self._ast_to_obj(data['signature']),
            user=self._ast_to_obj(data['user']),
            expiration=self._ast_to_obj(data['expiration']),
        )

    def _ast_to_datetime(self, data):
        return datetime.fromisoformat(data['datetime']) #converte la stringa ISO in un oggetto datetime

    def _ast_to_role(self, data):
        return Role[self._ast_to_obj(data['name'])]

    def _ast_to_request(self, data):
        return Request(
            service=self._ast_to_obj(data['service']), #aggiunto
            name=self._ast_to_obj(data['name']),
            args=tuple(self._ast_to_obj(arg) for arg in data['args']),
            authentication_token=self._ast_to_obj(data['authentication_token']) #aggiunto
        )

    def _ast_to_response(self, data):
        return Response(
            result=self._ast_to_obj(data['result']) if data['result'] is not None else None,
            error=self._ast_to_obj(data['error']),
        )

DEFAULT_SERIALIZER = Serializer()
DEFAULT_DESERIALIZER = Deserializer()

def serialize(obj): #serializza un oggetto in stringa
    return DEFAULT_SERIALIZER.serialize(obj)


def deserialize(string): #deserializza una stringa in oggetto
    return DEFAULT_DESERIALIZER.deserialize(string)

# Esempio di utilizzo : serializzazione e deserializzazione di una Request

if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_wrong

    request = Request(
        service='UserDatabase', # aggiunto
        name='my_function',
        args=(
            gc_credentials_wrong, # un istanza di Credentials
            gc_user, # un istanza di User
            ["a string", 42, 3.14, True, False], # una lista, contenente vari tipi primitivi
            {'key': 'value'}, # un dizionario
            Response(None, 'an error'), # una Response, che contiene un campo None
        )
    )
    serialized = serialize(request) 
    print("Serialized", "=", serialized)
    deserialized = deserialize(serialized)
    print("Deserialized", "=", deserialized)
    assert request == deserialized
