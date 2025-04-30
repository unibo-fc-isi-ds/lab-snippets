import socket
import pytest
from snippets.lab4.example2_rpc_server import ServerStub
from snippets.lab4.example3_rpc_client import *

import time





@pytest.fixture(scope="module", autouse=False)
def init_server():
    server = ServerStub(8080, suppress_error_log=True)
    yield server
    server.close()


@pytest.fixture(scope="module", autouse=False)
def init_user_data():
    user_1 = User(
        username='gciatto',
        emails={'giovanni.ciatto@unibo.it', 'giovanni.ciatto@gmail.com'},
        full_name='Giovanni Ciatto',
        role=Role.ADMIN,
        password='my secret password',
    )

    yield user_1



@pytest.fixture(scope="function", autouse=True)
def test_state(init_server, init_user_data):

    addr = address('localhost', 8080)
    
    user_db = RemoteUserDatabase(addr)
    user_auth_service = RemoteAuthenticationService(addr)


    yield {
        "user_data": init_user_data,
        "server": init_server,
        "user_db": user_db,
        "user_auth_service": user_auth_service
    }

    #after each test, clear the the user_db
    init_server.auth_service.user_db.clear()



   
    


def test_user_get(test_state):

    user = test_state["user_data"]


    with pytest.raises(RuntimeError, match="User with ID gciatto not found"):
        test_state["user_db"].get_user('gciatto')

    

    test_state["user_db"].add_user(user)

    assert test_state["user_db"].get_user('gciatto') == user.copy(password=None)






def test_user_add(test_state):


    user = test_state["user_data"]

    #
    expected_errors = [
        f"User with ID {user.username} already exists",
    ] + [f"User with ID {email} already exists" for email in user.emails]




    test_state["user_db"].add_user(user)

    with pytest.raises(RuntimeError) as exc_info:
        test_state["user_db"].add_user(user)

    _assert_error_message_in_pool(exc_info, expected_errors)






def test_user_check_password(test_state): 
    user = test_state["user_data"]

    test_state["user_db"].add_user(user)

    real_password = user.password

    assert test_state["user_db"].check_password(Credentials(user.username, real_password)) == True

    wrong_password = _permute_to_different_string(real_password)

    assert test_state["user_db"].check_password(Credentials(user.username, wrong_password)) == False



def test_token_expiration(test_state):

        user = test_state["user_data"]
    
        test_state["user_db"].add_user(user)
    
        real_password = user.password
    
        token = test_state["user_auth_service"].authenticate(Credentials(user.username, real_password), timedelta(days=1))

        assert token.expiration > datetime.now()

        short_lived_token = test_state["user_auth_service"].authenticate(Credentials(user.username, real_password), timedelta(seconds=1))

        time.sleep(1.2)

        assert test_state["user_auth_service"].validate_token(short_lived_token) == False




def test_token_authentication(test_state):
    
        user = test_state["user_data"]
    
        test_state["user_db"].add_user(user)
    
        real_password = user.password
    
        token = test_state["user_auth_service"].authenticate(Credentials(user.username, real_password), timedelta(days=1))
    

        assert test_state["user_auth_service"].validate_token(token) == True

        wrong_token = Token(user, token.expiration, _permute_to_different_string(token.signature))

        assert test_state["user_auth_service"].validate_token(wrong_token) == False




def _assert_error_message_in_pool(exc_info, expected_errors):
    error_message = str(exc_info.value)
    assert any(expected_error in error_message for expected_error in expected_errors), \
        f"Error message '{error_message}' not in expected pool"
    

def _permute_to_different_string(data: str, ascii_shift=50):
    return ''.join(chr((ord(char) + ascii_shift) % 127) for char in data)


    










