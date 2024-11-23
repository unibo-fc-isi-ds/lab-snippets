# Exercise: RPC-based Authentication Service

## Introduction
This project is a JSON-based RPC Authentication Service, enabling user authentication and token validation. Users can be authenticated only if pre-registered in the database, with all interactions handled via a command-line interface.

## Assumptions and limitations
- All users must be inserted into the database before authentication

## High Level Design
The provided structure of the RPC Client and Server has been adhered to, with the following additions:
- Serialization and deserialization of the timestamp for the token
- Implementation of the ClientStub code for the authentication service to handle "authentication" and "validate_token" requests
- Inclusion of the "service" field in the Request to direct requests to the appropriate service
- Addition of token saving in JSON files (formatted as {USERNAME}.json) after authentication.
- Addition of user saving in a JSON file (located in users/database) after users are added to the database. This file is read at server start-up to retrieve users added in previous sessions.


### Example
Run server on port 8080
```
poetry run python -m snippets -l 4 -e 2 8080
```

Add new user to database
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 add --user lucia --email test@gmail.com --name "Lucia Castellucci" -r admin -p "tell_nobody"
```

Run authentication for user just inserted
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 authenticate -u lucia -p "tell_nobody"
```

Token validation for user just authenticated
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 validate_token -u lucia
```

## Testing
The system has been tested in two distinct scenarios:
- **Success Scenario**: A new user is added to the database and attempts to authenticate. The goal is to ensure that the authentication is successful. To verify this, the authentication service is invoked using valid credentials. The test expects the response to be a token.
- **Failure Scenario**: The authentication service is invoked using invalid credentials, with no user having that username previously added to the database. The goal is to ensure that the authentication fails. The test expects a RuntimeError.

To run all the tests, you may exploit the following command:

```
poetry run poe test
```

Or simply run a specific test with:

```
poetry run python -m unittest discover -s tests -p "test_auth_successful.py"

poetry run python -m unittest discover -s tests -p "test_auth_unsuccessful.py"
```

The system has been tested on Windows, although Github Actions were used to ensure proper functionality on both MacOS and Linux environments. 
However a problem has been encountered with Windows and Python 12.