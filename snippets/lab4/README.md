## ES RPC PART 2 ##
+ ``` example1_presentation.py ```
I've implemented added the `metadata` field to Request class, and also to the `_request_to_ast` and `_ast_to_request` methods.


+ ``` example2_rpc_server.py ```
Now the `__on_message_event` method checks the authorization for `get_user` requests. It checks that the token is valid and the user is and `Admin`. If one of these conditions is not met, the Server retuns an `Unathorized` response.


+ ``` example3_rpc_client.py ```
The `RemoteAuthenticationService` now posses a `store_token` method, which stores a token in a file using the specific serialization and deserialization methods from Serializer/Deserializer classes. Each time the `ClientStub` is launched, it searches for a file named `token.txt` and reads it if present. The token is now sent with each subsequent request.


+ ``` example4_rpc_client_cli.py ```
The script now immediately stores the token after a successful authentication to the server. The validate request is now fully implemented, it send the token to the server and prints the result. 


NOTE: the token is always stored in `token.txt`, therefore the ClientStub keeps track only of the last generated token, previous token get lost. Namely, if I authenticate user A and then user B with the CLI, the token of A is overwritten by B the token of B. Therefore, subsequent request will use B's token (and it's capabilities). This is what happen in the test example below. 


### TESTING ###

In one terminal, launch the server like this: 
```
python -m snippets -l 4 -e 2 8080
```


In another terminal, use the client CLI to create and admin user: 
```
python -m snippets -l 4 -e 4 0.0.0.0:8080 add -u gciatto -a giovanni.ciatto@unibo.it giovanni.ciatto@gmail.com -n "Giovanni Ciatto" -r admin -p "my secret password"
```


Then create a non-admin user: 
```
python -m snippets -l 4 -e 4 0.0.0.0:8080 add -u mario -a mario.mario@unibo.it mario.mario@gmail.com -n "mario mario" -r user -p "password"
```


Authenticate the admin user (generate token):
```
python -m snippets -l 4 -e 4 0.0.0.0:8080 authenticate -u gciatto -p "my secret password"
```


Validate the admin token:
```
python -m snippets -l 4 -e 4 0.0.0.0:8080 validate -u gciatto
```


Retrive user's info thanks to admin capabilities: 
```
python -m snippets -l 4 -e 4 0.0.0.0:8080 get -u mario
```


Now authenticate the non-admin user (generate token):
```
python -m snippets -l 4 -e 4 0.0.0.0:8080 authenticate -u mario -p "password"
```


Validate the non-admin token:
```
python -m snippets -l 4 -e 4 0.0.0.0:8080 validate -u mario
```


Get `Unauthorized` message when trying to retrive user's information (we are now using the non-admin token):
```
python -m snippets -l 4 -e 4 0.0.0.0:8080 get -u gciatto
```
