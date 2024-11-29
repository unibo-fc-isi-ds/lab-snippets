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
