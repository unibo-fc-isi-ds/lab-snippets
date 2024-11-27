# Exercise: Secure RPC-based Authentication Service

## Introduction
This project extends the JSON-based RPC Authentication Service by adding access control features. More specifically, users can read from the database only if they are authenticated and if their role is admin. 

## High Level Design
The existing structure of the RPC-based Authentication Service has been adhered to, with the following additions:
- Inclusion of the `token` field in the `Request` class and update the corresponding (de)serialization logic
- Extension of the command-line interface by adding a new command to specify the requester of the operation
- Addition of the (optional) token in `ClientStub` 
- Distinction between protected and public operations via `@requires_authorization` decorator
- Update `ServerStub` to check for the presence and validity of the token and the user's role

### Example
Run server on port 8080:
```
poetry run python -m snippets -l 4 -e 2 8080
```

Add new users to the database:
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 add --user luca --email luca@gmail.com --name "Luca Samorè" -r admin -p "tell_nobody"

poetry run python -m snippets -l 4 -e 4 localhost:8080 add --user lucia --email lucia@gmail.com --name "Lucia Castellucci" -r user -p "tell_nobody"
```

Authenticate a user:
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 authenticate -u luca -p "tell_nobody"
```

Get a user:
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 get -d luca -u lucia
```

Check password:
```
poetry run python -m snippets -l 4 -e 4 localhost:8080 check -u luca
```

## Testing
**Happy Paths**:
- Authenticated admin user requests get on existing user
- Authenticated admin user requests password check

**Wrong Paths**:
- Authenticated non-admin user requests get on existing user
- Authenticated non-admin user requests password check
- Authenticated admin user requests get on non-existing user
- Admin user without token requests get on user
- Admin user without token requests password check
- Admin user with expired token requests get on user
- Admin user with expired token requests password check

To run all the tests, you may exploit the following command:

```
poetry run poe test
```

Or simply run a specific test with:

```
poetry run python -m unittest discover -s tests -p "test_authenticated_admin.py"

poetry run python -m unittest discover -s tests -p "test_authenticated_user.py"

poetry run python -m unittest discover -s tests -p "test_unauthenticated_admin.py"
```

The system has been tested on macOS, although Github Actions were used to ensure proper functionality on both Windows and Linux environments.