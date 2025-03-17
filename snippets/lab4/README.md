ex : RPC Auth Service

In this homework assignment, I augmented the RPC infrastructure with authentication services and enhanced some system functionality:
Enhanced Serialization/Deserialization

example1_presentation.py
Added serialization/deserialization of Token and Role objects while preserving the fields correctly (e.g., user, expiration, enums such as <Role.USER: 2>).
Better handling for User objects so that when data is marshaled and unmarshaled, no information is lost.
Implemented Server Logic

example2_rpc_server.py
Augmented ServerStub to handle RPC methods add_user, authenticate, and validate_token.
Enhanced \_\_handle_request to perform service routing in a more dynamic way, provide detailed debugging and refine error handling.
Combined InMemoryUserDatabase and InMemoryAuthenticationService.
Added updated Client Stubs

example3_rpc_client.py
Added RemoteAuthenticationService to perform authentication methods, namely authenticate and validate_token.
Improved the RemoteUserDatabase for performing user database management with robust error handling.
Improved CLI

example4_rpc_client_cli.py
Added add, auth, and validate for user management and authentication purposes.
Added additional argument parsing and error handling to help the user more.

For the Test:
1-Start the Server:
python example2_rpc_server.py 8080
2-add a user :
python example4_rpc_client_cli.py 127.0.0.1:8080 add --user kalile --email kalile@gmail.com --name "kalile horri" --role user --password secret
3-Authenticate the User :
python example4_rpc_client_cli.py 127.0.0.1:8080 auth --user kalile --password secret
4-Validate the Token:
python example4_rpc_client_cli.py 127.0.0.1:8080 validate

Exercise: RPC Auth Service 2

--example1_presentation.py--

This is responsible for softwares’ serialization and deserialization for the RPC system.

This project contains both serialisation and deserialisation for Token and User objects.

Role fields were made simpler (e.g., <Role.ADMIN: 1>).

Error text has been changed into one that is more suitable for an unsupported data type.

--example2_rpc_server.py--

Implements the ServerStub interface to undertake the RPC.

get, add_user, authenticate, and validate_token methods were added.

Revised \_\_handle_request so that any requests are directed to either the user or authentication service as appropriate.

Comprehensive auditing and role based data access control to allow only administrators view the information.

--example3_rpc_client.py --

Turns in client stubs so as to communicate with the server.

RemoteAuthenticationService was added for:

authenticate: Authenticates, with an NPC and get a Token.

validate_token: Token validation.

Appended RemoteUserDatabase for creating users and getting data with authorization.

Error reporting for server response is more elaborate now.

--example4_rpc_client_cli.py -

This is a command line interface for the purpose of carrying out system tests.

New commands were added to the command list within the program:

add: Add – add a new user (-‐user – email, name, role, password).

auth: Authorisation and obtaining a token.

validate: Validate a token.

get: Gets user details (only admin).

The tokens will now be stored and reused to allow for authorized requests.

Similar to all the other programs, detailed error messages and logs to aid in debugging have been added.

for the test:

1-Start the Server:
python example2_rpc_server.py 8080
2-Add a User:

python example4_rpc_client_cli.py 127.0.0.1:8080 add --user admin --email admin@example.com --name "Admin User" --role admin --password admin123

3-Authenticate as Admin:
python example4_rpc_client_cli.py 127.0.0.1:8080 auth --user admin --password admin123

Validate Token:
python -m snippets.lab4.example4_rpc_client_cli 127.0.0.1:8080 validate

4-Get User Data as Admin:
python example4_rpc_client_cli.py 127.0.0.1:8080 get --user admin

5-Unauthorized Access: Authenticate as a non-admin user and attempt to retrieve user data:
python example4_rpc_client_cli.py 127.0.0.1:8080 auth --user regular_user --password user123
python example4_rpc_client_cli.py 127.0.0.1:8080 get --user admin
