from .users import User, Credentials, Token, Role
from datetime import datetime
import json
from dataclasses import dataclass


# un nuovo dataclass che ha come campi il nome e una serie di argomenti passati, serve per fare richieste RPC
@dataclass
class Request:
    """
    A container for RPC requests: a name of the function to call and its arguments.
    """

    # ho aggiunto serviceType per distinguere il tipo di servizio (lavoro su database o lavoro di autenticazione)
    name: str
    serviceType: str
    args: tuple

    def __post_init__(self):
        self.args = tuple(self.args)


# dataclass che contiene un possibile risultato o errore, contiene le risposte di una richiesta mandata in sistema RPC
@dataclass
class Response:
    """
    A container for RPC responses: a result of the function call or an error message.
    When error is None, it means there was no error.
    Result may be None, if the function returns None.
    """

    result: object | None
    error: str | None

# la classe utilizzata per serializzare i dati (marshalling), dove trasformo oggetti in memoria in sequenze di bytes/caratteri
class Serializer:
    primitive_types = (int, float, str, bool, type(None))
    container_types = (list, set)

    # converte prima ogg in ast, poi ast in una stringa
    def serialize(self, obj): 
        return self._ast_to_string(self._to_ast(obj))

    # il metodo che trasforma i dati passati di AST in stringa
    def _ast_to_string(self, data):
        return json.dumps(data, indent=2)

    # tengo d'occhio di diversi corner cases
    def _to_ast(self, obj):
        # magari l'oggetto da serializzare fa parte dei tipi che considero primitivi all'inizio della classe
        if isinstance(obj, self.primitive_types):
            return obj # questi li mappo direttamente
        # il secondo caso si riferisce a tutti gli oggetti che considero "containers" (list e set)
        if isinstance(obj, self.container_types):
            return [self._to_ast(item) for item in obj] # mappo ogni oggetto del "container", creando un JSON array
        # il terzo caso si riferisce agli oggetti strutturati in maniera dictionary
        if isinstance(obj, dict):
            return {key: self._to_ast(value) for key, value in obj.items()} # mappo come Oggetto JSON (chiave uguale, valori trasformati)
        # quando trovo un oggetto più complesso (esempio, Credentials)
        # cerca prima di tutto di vedere qual'è il nome del tipo dell'oggetto passato (messo poi lowercase)
        # dentro method_name, scrivo così il nome del metodo. Python usa reflection per trasformare tale nome
        # in una chiamata a metodo con tale nome
        method_name = f'_{type(obj).__name__.lower()}_to_ast'
        if hasattr(self, method_name):
            # usando getattr recupero un riferimento al metodo da applicare a quell'oggetto (es:CREDENTIALS)
            data = getattr(self, method_name)(obj)
            # il dato ottenuto è così un oggetto JSON, a cui infine aggiungo un ultimo dato $type dove indico il tipo di dato
            data['$type'] = type(obj).__name__
            return data
        raise ValueError(f"Unsupported type {type(obj)}")

    # trasforma i dati di tipo utente in dati AST trasformabili poi in stringhe
    def _user_to_ast(self, user: User):
        return {
            'username': self._to_ast(user.username),
            'emails': [self._to_ast(email) for email in user.emails],
            'full_name': self._to_ast(user.full_name),
            'role': self._to_ast(user.role),
            'password': self._to_ast(user.password),
        }

    # trasforma i dati di tipo credenziali in dati AST trasformabili poi in stringhe
    def _credentials_to_ast(self, credentials: Credentials):
        return {
            'id': self._to_ast(credentials.id),
            'password': self._to_ast(credentials.password),
        }

    # trasforma i dati di tipo token in dati AST trasformabili poi in stringhe
    def _token_to_ast(self, token: Token):
        return {
            'signature': self._to_ast(token.signature),
            'user': self._to_ast(token.user),
            'expiration': self._to_ast(token.expiration),
        }

    # trasforma i dati di tipo datetime in dati AST trasformabili poi in stringhe
    def _datetime_to_ast(self, dt: datetime):
        return {'datetime': dt.isoformat()}

    # trasforma i dati di tipo ruolo in dati AST trasformabili poi in stringhe
    def _role_to_ast(self, role: Role):
        return {'name': role.name}

    # trasforma i dati di tipo richiesta in dati AST trasformabili poi in stringhe
    def _request_to_ast(self, request: Request):
        return {
            'name': self._to_ast(request.name),
            'serviceType': self._to_ast(request.serviceType),
            'args': [self._to_ast(arg) for arg in request.args],
        }

    # trasforma i dati di tipo risposta in dati AST trasformabili poi in stringhe
    def _response_to_ast(self, response: Response):
        return {
            'result': self._to_ast(response.result) if response.result is not None else None,
            'error': self._to_ast(response.error),
        }


# la classe utilizzata per deserializzare i dati (unmarshalling), dove trasformo sequenze di bytes/caratteri in oggetti in-memory
class Deserializer:
    # i processi qui sono invertiti, trasformo la stringa in un AST e poi l'AST in oggetti
    def deserialize(self, string):
        return self._ast_to_obj(self._string_to_ast(string))

    # metodo per trasformare la stringa in AST
    def _string_to_ast(self, string):
        return json.loads(string)

    # tutti i diversi corner cases per trasformare parti di AST in oggetti
    def _ast_to_obj(self, data):
        # se il dato AST passato è un dictionary, devo verificare che tipo di dictionary sia
        if isinstance(data, dict):
            # se il dato di AST passato non ha un campo/attributo "$type", allora vuol dire
            # che è un oggetto JSON di tipo dictionary (che contiene solo valori primitivi)
            # trasformo semplicemente i valori, lasciando chiave invariata
            if '$type' not in data:
                return {key: self._ast_to_obj(value) for key, value in data.items()}
            # quando trovo un oggetto più complesso (esempio, Credentials)
            # cerca prima di tutto di vedere qual'è il nome del tipo dell'oggetto passato (messo poi lowercase)
            # dentro method_name, scrivo così il nome del metodo. Python usa reflection per trasformare tale nome
            # in una chiamata a metodo con tale nome
            method_name = f'_ast_to_{data["$type"].lower()}'
            if hasattr(self, method_name): # se trova tale nome come metodo, applica il metodo al dato indicato
                return getattr(self, method_name)(data)
            raise ValueError(f"Unsupported type {data['type']}")
        if isinstance(data, list):
            return [self._ast_to_obj(item) for item in data]
        return data

    # trasforma dato AST in oggetto User
    def _ast_to_user(self, data):
        return User(
            username=self._ast_to_obj(data['username']),
            emails=set(self._ast_to_obj(data['emails'])),
            full_name=self._ast_to_obj(data['full_name']),
            role=self._ast_to_obj(data['role']),
            password=self._ast_to_obj(data['password']),
        )

    # trasforma dato AST in oggetto Credentials
    def _ast_to_credentials(self, data):
        return Credentials(
            id=self._ast_to_obj(data['id']),
            password=self._ast_to_obj(data['password']),
        )

    # trasforma dato AST in oggetto Token
    def _ast_to_token(self, data):
        return Token(
            signature=self._ast_to_obj(data['signature']),
            user=self._ast_to_obj(data['user']),
            expiration=self._ast_to_obj(data['expiration']),
        )

    # trasforma dato AST in oggetto di tipo datetime
    def _ast_to_datetime(self, data):
        return datetime.fromisoformat(data['datetime'])

    # trasforma dato AST in oggetto Role
    def _ast_to_role(self, data):
        return Role[self._ast_to_obj(data['name'])]

    # trasforma dato AST in oggetto Request
    def _ast_to_request(self, data):
        return Request(
            name=self._ast_to_obj(data['name']),
            serviceType=self._ast_to_obj(data['serviceType']),
            args=tuple(self._ast_to_obj(arg) for arg in data['args']),
        )

    # trasforma dato AST in oggetto Response
    def _ast_to_response(self, data):
        return Response(
            result=self._ast_to_obj(data['result']) if data['result'] is not None else None,
            error=self._ast_to_obj(data['error']),
        )


DEFAULT_SERIALIZER = Serializer()
DEFAULT_DESERIALIZER = Deserializer()


def serialize(obj):
    return DEFAULT_SERIALIZER.serialize(obj)


def deserialize(string):
    return DEFAULT_DESERIALIZER.deserialize(string)


if __name__ == '__main__':
    from snippets.lab4.example0_users import gc_user, gc_credentials_wrong

    request = Request(
        name='my_function',
        args=(
            gc_credentials_wrong, # an instance of Credentials
            gc_user, # an instance of User
            ["a string", 42, 3.14, True, False], # a list, containing various primitive types
            {'key': 'value'}, # a dictionary
            Response(None, 'an error'), # a Response, which contains a None field
        )
    )
    serialized = serialize(request)
    print("Serialized", "=", serialized)
    deserialized = deserialize(serialized)
    print("Deserialized", "=", deserialized)
    assert request == deserialized
