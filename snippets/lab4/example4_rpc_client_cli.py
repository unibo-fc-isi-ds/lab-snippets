from snippets.lab4.example3_rpc_client import *
import argparse
import sys

TEST_USERNAME = "Carlo"
TEST_EMAIL = "carlo@carlo.it"
TEST_FULL_NAME = "CarloCarlo"
TEST_CORRECT_PASS = "carlo"
TEST_FAKE_PASS = "carlone"
TEST_SERVER_PORT = 8080

def test_add_user():
    user_db_auth = RemoteUserDatabaseAndAuthentication(address(port=TEST_SERVER_PORT))
    user = User(TEST_USERNAME, TEST_EMAIL, TEST_FULL_NAME,
                Role.USER, TEST_CORRECT_PASS)
    user_without_pass = User(TEST_USERNAME, TEST_EMAIL, TEST_FULL_NAME,
                Role.USER)
    user_db_auth.add_user(user)
    obtained_user = user_db_auth.get_user(TEST_USERNAME)
    assert obtained_user == user_without_pass

def test_check_pass_correct_user():
    user_db_auth = RemoteUserDatabaseAndAuthentication(address(port=TEST_SERVER_PORT))
    credentials = Credentials(TEST_USERNAME, TEST_CORRECT_PASS)
    assert user_db_auth.check_password(credentials=credentials)

def test_check_pass_fake_user():
    user_db_auth = RemoteUserDatabaseAndAuthentication(address(port=TEST_SERVER_PORT))
    credentials = Credentials(TEST_USERNAME, TEST_FAKE_PASS)
    assert not user_db_auth.check_password(credentials=credentials)

def test_authenticate_user():
    user_db_auth = RemoteUserDatabaseAndAuthentication(address(port=TEST_SERVER_PORT))
    credentials = Credentials(TEST_USERNAME, TEST_CORRECT_PASS)
    token = user_db_auth.authenticate(credentials=credentials, 
                                      duration=timedelta(days=1))
    assert user_db_auth.validate_token(token)
    

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
    parser.add_argument('--token', '-t', help='Token')
    parser.add_argument('--expiration', help='Expiration date token')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db_auth = RemoteUserDatabaseAndAuthentication(args.address)

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
                print(user_db_auth.authenticate(credentials))
            case 'validate_token':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                token = Token(user, datetime.fromisoformat(args.expiration), 
                              args.token)
                print(user_db_auth.validate_token(token))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
