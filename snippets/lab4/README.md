# Exercise: RPC-based Authentication Service

## Introduction
This project is a JSON-based RPC Authentication Service, enabling user authentication and token validation. Users can be authenticated only if pre-registered in the database, with all interactions handled via a command-line interface.

## Assumptions and Limitations
- All users must be inserted into the database before authentication

## High Level Design
The provided structure of the RPC Client and Server has been adhered to, with the following additions:
- Serialization and deserialization of the expiration datetime of the token
- Implementation of the ClientStub code for the authentication service to handle `authenticate` and `validate_token` requests
- Inclusion of the `service` field in the `Request` class to direct requests to the appropriate service (i.e. UserDatabase or AuthenticationService)
- Addition of token saving in JSON files (formatted as `<username>.json`) after authentication. All these files are stored in the `./snippets/lab4/tokens/` directory
- Addition of user saving in a JSON file (located in `./snippets/lab4/database.json`) after users are inserted to the database. This file is read at server start-up to retrieve users added in previous sessions
- Extraction of the signature creation logic to a separate class (`DefaultSigner`), allowing testing of the token validation feature


### Example
Run server on port 8080:
```
poetry run python -m snippets -l 4 -e 2 8080
```

Add a new user to the database:
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 add --user lucia --email test@gmail.com --name "Lucia Castellucci" -r admin -p "tell_nobody"
```

Authenticate a user:
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 authenticate -u lucia -p "tell_nobody"
```

Validate user token:
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 validate_token -u lucia
```

## Testing
The system has been tested in the following scenarios:
- **Authentication is successful scenario**: a new user is added to the database and attempts to authenticate. The goal is to ensure that the authentication process is successful. To verify this, the authentication service is invoked using valid credentials. The test expects the response to be a `Token`
- **Authentication is unsuccessful scenario**: the authentication service is invoked using invalid credentials (i.e. id and/or password), with no user in the database having that id. The goal is to ensure that the authentication process fails. The test expects a `RuntimeError`
- **Token is valid scenario**: assuming the user is already authenticated, the authentication service is invoked by passing the user's token. The service verifies whether the token is valid, i.e., it is not expired and its signature is correct. The test expects a return value of `True`
- **Token is invalid scenario**: the authentication service is invoked by passing a bad token, i.e.
    - an expired token
    - a token with an invalid signature

    The test expects a return value of `False`

To run all the tests, you may exploit the following command:

```
poetry run poe test
```

Or simply run a specific test with:

```
poetry run python -m unittest discover -s tests -p "test_auth_successful.py"

poetry run python -m unittest discover -s tests -p "test_auth_unsuccessful.py"

poetry run python -m unittest discover -s tests -p "test_token_is_valid.py"

poetry run python -m unittest discover -s tests -p "test_token_is_invalid.py"
```

The system has been tested on Windows, although Github Actions were used to ensure proper functionality on both MacOS and Linux environments.