from snippets.lab4.example3_rpc_client import *
import argparse, sys, pytest
from snippets.lab4.example1_presentation import serialize, deserialize

# START TEST CONSTANTS AND VARIABLES
TEST_USERNAME = "Carlo"
TEST_EMAIL: str = "carlo@carlo.it"
TEST_FULL_NAME = "CarloCarlo"
TEST_CORRECT_PASS = "carlo"
TEST_FAKE_PASS = "marco"
TEST_UNAUTH_USERNAME = "Giovanni"
TEST_UNAUTH_EMAIL: str = "giovanni@giovanni.it"
TEST_UNAUTH_FULL_NAME = "GiovanniGiovanni"
TEST_UNAUTH_PASS = "giovanni"
TEST_SERVER_PORT = 8080
token_test = None
# END TEST CONSTANTS AND VARIABLES

class TestGroup():
    # Add Admin user, authenticate, then get user
    def test_add_user(self):
        user_db_auth = RemoteUserDatabaseAndAuthentication(address(port=TEST_SERVER_PORT), None)
        user = User(TEST_USERNAME, {TEST_EMAIL}, TEST_FULL_NAME,
                    Role.ADMIN, TEST_CORRECT_PASS)
        user_without_pass = User(TEST_USERNAME, {TEST_EMAIL}, TEST_FULL_NAME,
                    Role.ADMIN)
        user_db_auth.add_user(user)
        credentials = Credentials(TEST_USERNAME, TEST_CORRECT_PASS)
        token_test = user_db_auth.authenticate(credentials=credentials, 
                                        duration=timedelta(days=1))
        user_db_auth = RemoteUserDatabaseAndAuthentication(address(port=TEST_SERVER_PORT), token_test)
        obtained_user = user_db_auth.get_user(TEST_USERNAME)
        assert obtained_user == user_without_pass

    # Check correct password
    def test_check_pass_correct_user(self):
        user_db_auth = RemoteUserDatabaseAndAuthentication(address(port=TEST_SERVER_PORT), token_test)
        credentials = Credentials(TEST_USERNAME, TEST_CORRECT_PASS)
        assert user_db_auth.check_password(credentials=credentials)

    # Check incorrect password
    def test_check_pass_fake_user(self):
        user_db_auth = RemoteUserDatabaseAndAuthentication(address(port=TEST_SERVER_PORT), token_test)
        credentials = Credentials(TEST_USERNAME, TEST_FAKE_PASS)
        assert not user_db_auth.check_password(credentials=credentials)

    # Authenticate admin
    def test_authenticate_user(self):
        user_db_auth = RemoteUserDatabaseAndAuthentication(address(port=TEST_SERVER_PORT), token_test)
        credentials = Credentials(TEST_USERNAME, TEST_CORRECT_PASS)
        token = user_db_auth.authenticate(credentials=credentials, 
                                        duration=timedelta(days=1))
        assert user_db_auth.validate_token(token)

    # Create user with low authorization and try to access data without permission
    def test_unauth_user(self):
        user_db_auth = RemoteUserDatabaseAndAuthentication(address(port=TEST_SERVER_PORT), None)
        user = User(TEST_UNAUTH_USERNAME, {TEST_UNAUTH_EMAIL}, TEST_UNAUTH_FULL_NAME,
                    Role.USER, TEST_UNAUTH_PASS)
        user_db_auth.add_user(user)
        credentials = Credentials(TEST_UNAUTH_USERNAME, TEST_UNAUTH_PASS)
        token_test = user_db_auth.authenticate(credentials=credentials, 
                                        duration=timedelta(days=1))
        user_db_auth.validate_token(token_test)
        with pytest.raises(RuntimeError):
            user_db_auth.get_user(TEST_USERNAME)


def checkInstanceToken(token: Token):
    if (isinstance(token, Token)):
        return
    else:
        print("Invalid token file")
        sys.exit(1)

# Check if token file exists, None is return otherwise
def retrieveTokenFile(fileName: str = "token.json") -> Token:
    if (not fileName):
        fileName = "token.json"
    try:
        f = open(fileName, "r")
    except OSError as e:
        return None
    with f:
        tokenFile = f.read()
    token = deserialize(tokenFile)
    checkInstanceToken(token)
    return token

# Save a token
def saveTokenFile(token: Token, fileName: str = "token.json"):
    if (not fileName):
        fileName = "token.json"
    checkInstanceToken(token)
    try:
        f = open(fileName, "w")
    except OSError as e:
        print("Cannot create token file: " + str(e))
        sys.exit(1)
    with f:
        f.write(serialize(token))
    

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate', 'validate_token'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--filename', '-f', help='File Name')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db_auth = RemoteUserDatabaseAndAuthentication(args.address, retrieveTokenFile(args.filename))

    try :
        ids = (args.email or []) + [args.user]
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db_auth.add_user(user))
            case 'get':
                print(user_db_auth.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db_auth.check_password(credentials))
            case 'authenticate':
                credentials = Credentials(ids[0], args.password)
                token = user_db_auth.authenticate(credentials)
                saveTokenFile(token, args.filename)
                print(token)
            case 'validate_token':
                token = retrieveTokenFile(args.filename)
                print(user_db_auth.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
