# Exercise: RPC-based Authentication Service
Goal: extend the exemplified RPC infrastructure to support an authentication service
* The server now has an 'InMemoryAuthenticationService' instance as an attribute to delegate any authentication or token validation requests to.
* A new class 'RemoteAuthService' is provided that extends the 'ClientStub' and 'AuthenticationService' classes. This is the class responsible for sending requests to invoke the user authentication and token validation procedures.
* The client command line interface has been extended with the 'auth' and 'validate' commands. The 'auth' command requires the user's id and password parameters and accepts an additional parameter indicating the path and name of the file in which to store the token. The 'validate' command only requires the parameter indicating the path to the token file. 
* The Serializer's '_datetime_to_ast' method and the Deserializer's '_ast_to_datetime' method have been implemented to serialize and deserialize, respectively, a datetime object.


## Running the server

Start the server with:
```
poetry run python -m snippets -l 4 -e 2 PORT
```
where PORT is the port number the server will listen to, e.g. 8080

## Running the client

Authentication command:
```bash
python -m snippets -l 4 -e 4 SERVER_IP:PORT auth -u name -p password [-tp] [--tokenPath filepath]
```

Token validation command:
```bash
python -m snippets -l 4 -e 4 SERVER_IP:PORT validate -tp filepath
```
where:
* SERVER_IP (e.g. localhost) is the IP address of the server;
* PORT is the port number the server is listening to (e.g. 8080);
* name is the user's id;
* password is the user's password;
* filepath is the path of the file to store the token into. 
