from .users import *
from .users.impl import *
import time

_PRINT_LOGS = __name__ == '__main__'

user_db = InMemoryUserDatabase(debug=_PRINT_LOGS)
auth_service = InMemoryAuthenticationService(user_db, debug=_PRINT_LOGS)


gc_user = User(
    username='gciatto',
    emails={'giovanni.ciatto@unibo.it', 'giovanni.ciatto@gmail.com'},
    full_name='Giovanni Ciatto',
    role=Role.ADMIN,
    password='password',
)

gc_user_hidden_password = gc_user.copy(password=None)

gc_credentials_ok = [Credentials(id, gc_user.password) for id in gc_user.ids] # type: ignore

gc_credentials_wrong = Credentials(
    id='giovanni.ciatto@unibo.it',
    password='wrong password',
)

# Trying to get a user that does not exist should raise a KeyError
try:
    user_db.get_user('gciatto')
except KeyError as e:
    assert 'User with ID gciatto not found' in str(e)

# Adding a novel user should work
user_db.add_user(gc_user)

# Trying to add a user that already exist should raise a ValueError
try:
    user_db.add_user(gc_user)
except ValueError as e:
    assert str(e).startswith('User with ID')
    assert str(e).endswith('already exists')

# Getting a user that exists should work
assert user_db.get_user('gciatto') == gc_user.copy(password=None)

# Checking credentials should work if there exists a user with the same ID and password (no matter which ID is used)
for gc_cred in gc_credentials_ok:
    assert user_db.check_password(gc_cred) == True

# Checking credentials should fail if the password is wrong
assert user_db.check_password(gc_credentials_wrong) == False

# Authenticating with wrong credentials should raise a ValueError
try:
    auth_service.authenticate(gc_credentials_wrong)
except ValueError as e:
    assert 'Invalid credentials' in str(e)

# Authenticating with correct credentials should work
gc_token = auth_service.authenticate(gc_credentials_ok[0])
# The token should contain the user, but not the password
assert gc_token.user == gc_user_hidden_password
# The token should expire in the future
assert gc_token.expiration > datetime.now()

# A genuine, unexpired token should be valid
assert auth_service.validate_token(gc_token) == True

# A token with wrong signature should be invalid
gc_token_wrong_signature = gc_token.copy(signature='wrong signature')
assert auth_service.validate_token(gc_token_wrong_signature) == False

# A token with expiration in the past should be invalid
gc_token_expired = auth_service.authenticate(gc_credentials_ok[0], timedelta(milliseconds=10))
time.sleep(0.1)
assert auth_service.validate_token(gc_token_expired) == False
