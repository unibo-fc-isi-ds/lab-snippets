

#### ES RPC PART 1 ####
+ ``` example1_presentation.py ```
I've implemented the datetime serialization and deserialization functions, by simply using an ISO format.  

+ ``` example2_rpc_server.py ```
I've added an InMemoryAuthenticationService as a field in the ServerStub, then I've modified the ```__handle_request``` function, so that it will dispatch authentication requests to the ``AuthenticationService``.

+ ``` example3_rpc_client.py ```
I've written the ```RemoteAuthenticationService``` class, which inheriths from ```ClientStub``` and ```AuthenticationService```. It defines the ```authentication``` and ```validate_token``` method, which will be used to send authentication requests to the server.


+ ``` example4_rpc_client_cli.py ```
I've added the `authenticate` and `validate` commands to the CLI. They will call the corresponding methods of an instance of ```RemoteAuthenticationService``` class. The authenticate command requires in input the password as a command line argument.


Instead, the validate method is not fully implemented yet, because the token is not stored by the client. It's something that is implemented in the second part of the exercise. I've added to the CLI flags to receive the signature and the expiration of the token, in order to be able to mock a validate request by hand (the signature and the expiration are printed after the authentication).

#### TESTING ####

In one terminal, launch the server like this: 
```
python -m snippets -l 4 -e 2 8080
```


In another terminal, use the client CLI to create and authenticate and user: 
```
# Create an user
python -m snippets -l 4 -e 4 0.0.0.0:8080 add -u gciatto -a giovanni.ciatto@unibo.it giovanni.ciatto@gmail.com -n "Giovanni Ciatto" -r admin -p "my secret password"
```


Authenticate the user (generate token)
```
python -m snippets -l 4 -e 4 0.0.0.0:3000 authenticate -u gciatto -p "my secret password"
```



Validate the newly created token (mock)

```
python -m snippets -l 4 -e 4 0.0.0.0:3000 validate -u gciatto python -m snippets -l 4 -e 4 0.0.0.0:8080 add -u gciatto -a giovanni.ciatto@unibo.it giovanni.ciatto@gmail.com -n "Giovanni Ciatto" -r admin -p "my secret password" -e "2024-11-26 17:35:26.856975" -s mysignature
```