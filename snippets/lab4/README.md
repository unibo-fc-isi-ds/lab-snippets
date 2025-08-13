# Exercise: RPC-based Authentication Service 2
Goal: extend the exemplified RPC infrastructure to support authorization
* The Request class has been updated with a new field, metadata, which is a tuple that can be left empty.
* The server now validates the user's authentication before handling the get_user procedure. Specifically:
    * If no authentication token is provided, the server responds with an error: "Missing authentication token."
    * If the provided token is invalid, the server returns an error: "Request not allowed. Authentication required."
    * If the user is not an admin, the server responds with: "Request not allowed. User is not authorized."
* The client stores the authentication token received during login and includes it in subsequent get_user requests to the server.

## Running the server

Start the server with:
```
poetry run python -m snippets -l 4 -e 2 PORT
```
where PORT is the port number the server will listen to, e.g. 8080

## Running the client

Command to get the info of a user:
```bash
python -m snippets -l 4 -e 4 SERVER_IP:PORT get -u name -tp filepath
```

where:
* SERVER_IP (e.g. localhost) is the IP address of the server;
* PORT is the port number the server is listening to (e.g. 8080);
* name is the id of the user to get details of;
* filepath is the path of the file where the token is stored into. 
