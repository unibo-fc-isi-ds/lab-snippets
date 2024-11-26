# Exercise: RPC-based Authentication Service

## File update changes and explanation
* In the '''example1_presentation.py''', I added the serialization and deserialization functions for the datatime.

* In the '''example2_rpc_server.py''', I made it so that the authentication request is sent to the authentication service by changing the method __handle_request.

* In the '''example3_rpc_client.py''', I added the RemoteAuthenticationService class, so that now you can send an authentication request to the server using the methods: authenticate() and validate_token()

* In the '''example4_rpc_client_cli.py''', I added the authenticate and validate commands to the CLI, and managed the authenticate and validate cases, so that the authentication service is well implemented and functional.

## Testing phase
For testing follow this step:

1. Open one temrinal and launch: ''' python -m snippets -l 4 -e 2 8080 ''' to opena a server.
2. Open another terminal and launch: ''' python -m snippets -l 4 -e 4 localhost:8080 add -u giovapiso -a giovanni.pisoni@studio.unibo.it -n "Giovanni Pisoni" -r user -p "secret password" ''' to add a user.
3. Launch: ''' python -m snippets -l 4 -e 4 0.0.0.0:8080 authenticate -u giovapiso -p "secret password" --path giovanni-token.json ''' to generate the token and save it in a specific file and to authenticate the user.
4. Launch: ''' python -m snippets -l 4 -e 4 localhost:8080 validate --path mirco-token.json ''' to validate the newly created token

##### ATTENTION: 
> In the point 4 you can insert the token directly as an argument avoiding creating a specific file and using it.
