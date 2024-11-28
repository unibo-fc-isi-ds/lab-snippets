Changes:

In the example1_presentation.py:
Implemented datetime serialization functions.

In the example2_rpc_server.py:
Initialized InMemoryAuthenticationService in ServerStub and then modified __handle_request to process authenticate and validate_token requests.

In the example3_rpc_client.py:
Added the RemoteAuthenticationService class, so that now you can send an authentication request to the server using the methods: authenticate() and validate_token()

In the example4_rpc_client_cli.py:
Extended the authenticate and validate commands to the CLI, and handled cases for both commands within the CLI interface.

About Testing:

Open first terminal:
Launch: python -m snippets -l 4 -e 2 8080 //to start a server.
Open second terminal:
Launch: python -m snippets -l 4 -e 4 127.0.0.1:8080 add -u guojiahao -a jiahao.guo@studio.unibo.it -n "Jia hao Guo" -r user -p "my secret password" //to add a user.
Launch: python -m snippets -l 4 -e 4 127.0.0.1:8080 authenticate -u "guojiahao" -p "my secret password" --path gtoken.json //to generate the token and save it in a specific file.
Launch: python -m snippets -l 4 -e 4 127.0.0.1:8080 validate --path gtoken.json //to validate token

Alternative Token Validation:
You can also pass the token directly in the CLI:
Launch: python -m snippets -l 4 -e 4 127.0.0.1:8080 validate --token 'Token format argument'
