# Exercise: RPC-based Authentication Service

## Introduction
This is my solution for a possible JSON-based RPC Authentication Service, capable of user authentication and token validation. 
Each user can authenticate only after registering in the database, doing so thanks to a command-line interface. 

## Design
The solution is an extension of previously shown RPC Client and Server structure shown during previous lectures.
The current additions to the architecture are:
- Serialization and deserialization of the `datetime` expiration of the authentication tokens;
- Implementation in the ClientStub code of a `RemoteAuthenticationService` class in order to handle `authenticate` and `validate_token` requests;
- Addition of `serviceType` field in the `Request` dataclass to properly direct requests to the correct service (which are either `UserDatabase` or `AuthenticationService`);
- Implementation of a token saving feature in JSON files and token reading feature from JSON files. After completing the authentication, a new method `save_token` is called to store in the `./snippets/lab4/savedTokens/` directory the newly created token, which is formatted as `<username>.json`. When starting validation of token, method `read_token` is called to retrieve from directory a JSON file with the given `<username>`;

## Testing
Testing of current solution was done using both Command-Line and a new series of Test files which are stored in `testFiles` directory.

### Command-Line Testing
First we run the server on port `8080` using this command on a terminal:
```
poetry run python -m snippets -l 4 -e 2 8080
```

After that, a new terminal is opened, where we first must add at least one user in the database. Here's an example of a new addition in the database:
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 add --user abianchi --email andBianchi@gmail.com --name "Andrea Bianchi" -r admin -p "my_password"
```


In order to test the authentication service, we first must test the authentication feature to generate a new token. It's necessary to give `user` and `password` as `args` in the command line for it to succeed:
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 authenticate -u abianchi -p "my_password"
```

If the given `args` are correct, a new token will be generated (and the client CLI will display a message to let the user know about it). Finally, we validate the newly generated token with this command:
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 validate_token -u abianchi
```

The client CLI will send a `Your token is valid` message to confirm that it has succeeded, otherwise it will either capture an exception or send a `Your token is not valid. Generate a new one!` message if the token's not correct (due to having expired, not having the proper signature...)

### Unit Tests
Two new testing files have been created in order to check and test different scenarios and features.
Both files contain two `@classmethod` methods. These are:
- `def setUpClass`: before starting tests, the `ServerStub` is created, along with its `RemoteUserDatabase` and `RemoteAuthenticationService`. A new `user` is then added into the database;
- `def tearDownClass`: after finishing every test contained in the class, the server is gracefully closed.

The newly test files are:

- **FILE `test_authentication`**: In this file we focus on testing both how the RPC structure interacts in cases of both correct and wrong authentication. The file contains these 3 test functions:
    - `def test_authentication_successful`: A new `testCredentials` is created giving it the correct `username` and `password` of the one added into the database. Using `authenticate` function of the authentication service, we check whether the `returnedToken` is an actual instance of `Token` class (and not `None`);
    - `def test_authentication_failure`: This time a `testFailCredentials` is made that contains the `username` of the user in the database but the wrong password. We then capture any `RuntimeException` that is generated from the `authenticate` method;
    - `def test_authentication_failure_missingUser`: the failing `Credentials` object created has the incorrect `username`. Similarly to the previous method, we capture `RunTimeExceptions` generated;
- **FILE `test_validate_token`**: This file is centered around testing of method `validate_token` of the authentication service. While also containing the same `setUp` and `tearDown` of previous methods, it also has the `def __compute_sha256_hash` found in `impl.py` to hash the password, and 2 different test methods:
    - `def test_valid_token`: this method recalls the `authenticate` method to generate the new token for the user and then calls `validate_token` method to validate it, expecting `True` as the returned value;
    - `def test_incorrect_token`: a new token is generated that uses the wrong signature. It is given as a parameter to `validate_token`, where we assert that the returned value is `False`;
    - `def test_expired_token`: taking data from returnedToken of the `authenticate` method call, we create a new `Token` with an expired datetime, after which we assert that the returned value is `False`.

To run each specific test, these commands can be run through terminal:

```
poetry run python -m unittest discover -s tests -p "test_authentication.py"

poetry run python -m unittest discover -s tests -p "test_validate_token.py"
```

The system has been tested only on Windows environment.