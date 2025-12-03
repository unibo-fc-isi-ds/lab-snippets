from .users import *
from .users.impl import *
import time


_PRINT_LOGS = __name__ == '__main__'

# Creazione di un database utenti in memoria e di un servizio di autenticazione
user_db = InMemoryUserDatabase(debug=_PRINT_LOGS)
auth_service = InMemoryAuthenticationService(user_db, debug=_PRINT_LOGS)

# Creazione di un utente di test 
gc_user = User(
    username='gciatto',
    emails={'giovanni.ciatto@unibo.it', 'giovanni.ciatto@gmail.com'},
    full_name='Giovanni Ciatto',
    role=Role.ADMIN,
    password='my secret password',
)

# Creazione di una versione dell'utente senza password (usato per i confronti)
gc_user_hidden_password = gc_user.copy(password=None)

# Creazione di una lista di credenziali corrette create con tutti gli id dell'utente + password
# gli id sono username + emails
gc_credentials_ok = [Credentials(id, gc_user.password) for id in gc_user.ids] # type: ignore

# Creazione di credenziali errate
gc_credentials_wrong = Credentials(
    id='giovanni.ciatto@unibo.it',
    password='wrong password',
)

## --- TEST UTENTI --- ##

#Proviamo a fare la get di un utente che non esiste
try:
    user_db.get_user('gciatto')
except KeyError as e:
    assert 'User with ID gciatto not found' in str(e)

# Aggiunta di un nuovo utente dovrebbe funzionare
user_db.add_user(gc_user)

# Tentare di aggiungere un utente che esiste già dovrebbe sollevare un ValueError
try:
    user_db.add_user(gc_user)
except ValueError as e:
    assert str(e).startswith('User with ID')
    assert str(e).endswith('already exists')

# Ottenere l'utente appena aggiunto dovrebbe funzionare
assert user_db.get_user('gciatto') == gc_user.copy(password=None)

# Il controllo delle credenziali dovrebbe funzionare se esiste un utente con lo stesso ID e password (indipendentemente dall'ID usato)
for gc_cred in gc_credentials_ok:
    assert user_db.check_password(gc_cred) == True

# Il controllo delle credenziali dovrebbe fallire se la password è sbagliata
assert user_db.check_password(gc_credentials_wrong) == False


## --- TEST AUTENTICAZIONE --- ##

# L'autenticazione con credenziali errate dovrebbe sollevare un ValueError
try:
    auth_service.authenticate(gc_credentials_wrong)
except ValueError as e:
    assert 'Invalid credentials' in str(e)

# L'autenticazione con credenziali corrette dovrebbe restituire un token valido
gc_token = auth_service.authenticate(gc_credentials_ok[0])

# Il token dovrebbe contenere l'utente, ma non la password
assert gc_token.user == gc_user_hidden_password
# Il token dovrebbe scadere in futuro
assert gc_token.expiration > datetime.now()

# Un token genuino e non scaduto dovrebbe essere valido
assert auth_service.validate_token(gc_token) == True

#Un token con firma alterata dovrebbe essere invalido
gc_token_wrong_signature = gc_token.copy(signature='wrong signature')
assert auth_service.validate_token(gc_token_wrong_signature) == False

# Un token con scadenza nel passato dovrebbe essere invalido
gc_token_expired = auth_service.authenticate(gc_credentials_ok[0], timedelta(milliseconds=10))
time.sleep(0.1)
assert auth_service.validate_token(gc_token_expired) == False
