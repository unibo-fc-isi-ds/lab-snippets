# General description
The objective of these exercises was to improve the existing Remote User Database by implementing authentication and authorization.

Authentication was implemented by adding two commands, `authenticate` and `logout` while authorization is implemented in the `get` operation.

## Authentication
### authenticate
The client sends the authenticate command to the server with a username and password. If the credentials are correct, the server generates a token that verifies the client's identity.

This token is saved by the client on a file and it is used automatically in all operations needing an authentication token, such as `get` and `check`.

If the token is invalid because more than 2 hours have passed from the authentication or the token was altered, all operations needing the token will ask the user to authenticate again.

The token is serialized and deserialized using the same methods needed to communicate the token over the network.

### logout
Since the authentication token is saved on a file, a logout operation is necessary. This operation deletes the file where the authentication token is saved. 
This allows a user to log out securely, otherwise any user using the same computer after a logged-in user could employ someone else's token. Even if a token is not deleted manually with the logout operation, since it spoils after 2 hours, saving this token on file is less risky than a token with a longer life.

## Authorization
When creating a user, two roles are available: ADMIN and USER. Only ADMIN users can use the `get` operation, all other users will fail because of insufficient permissions. Since the `get` operation needs an authentication token, only **authenticated ADMIN users** can perform it.

# Running
This exercise all runs with a poetry local environment, so either start a poetry shell with `poetry shell` or prepend all commands with `poetry run`.

Start the server with:

`python -m snippets -l 4 -e 2 PORT`

On another shell, start the client by adding a user.
This is necessary as no operations can be performed without a user in the database.

`python -m snippets -l 4 -e 4 SERVER_IP:SERVER_PORT add -u USERNAME -a EMAILS -n "FULL NAME" -r ROLE -p "PASSWORD"`

- The Emails parameter can be as many email addresses as you want, with a space in between.
- The Role parameter must be either admin or user.

  
If the user is added successfully the client is shown "None"

To authenticate the command is as follows:

`python -m snippets -l 4 -e 4 SERVER_IP:SERVER_PORT authenticate -u ID -p PASSWORD`

- The ID parameter can be either the username or one of the user emails.

If authentication happens successfully the token is saved and all authentication operations can be performed.

The get and check commands have the same parameters as the original implementation, as the checking for authentication and authorization happens on the server automatically.

**The get command can only be performed by authenticated admin users.**

`python -m snippets -l 4 -e 4 SERVER_IP:SERVER_PORT get -u ID`

- The ID parameter can be either the username or one of the user emails.

The get command returns all the info of a saved User, without the password.

**The check command can only be performed by authenticated users.**

`python -m snippets -l 4 -e 4 SERVER_IP:SERVER_PORT check -u ID -p PASSWORD`

- The ID parameter can be either the username or one of the user emails.
  
The check command returns True if the username and password are correct, otherwise False.

The logout command simply is:

`python -m snippets -l 4 -e 4 SERVER_IP:SERVER_PORT logout`

If the user is logged in the token authentication file is deleted, otherwise nothing occurs.

# Running unit tests
To check the correct functioning of the system some unit tests have been implemented.
The command to run the unit tests in a poetry shell is:

`python -m unittest discover -s test`

The unit tests start a server on port 8081, so if any other shell is using the same port errors could occur.
