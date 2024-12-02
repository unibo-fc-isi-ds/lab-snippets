# Exercise: RPC-based Authentication Service

An extension of the exemplified RPC infrastructure has been created to support an authentication service.

In particular, the server stub delegates the actual work to an actual instance of InMemoryAuthenticationService. 

Another client stub has been created for the AuthenticationService interface.

The authenticate and validate commands have been added to the cli client, to perform authentication and authentication validation.

To start the server:

``` python -m snippets -l 4 -e 2 PORT ```

To authenticate in the client cli:

``` python -m snippets -l 4 -e 4 SERVER_PORT:PORT authenticate -u USER -p PASSWORD -t TOKEN_FILE_NAME```

If the file is not specified, token_file.json is used

To validate in the client cli:

``` python -m snippets -l 4 -e 4 localhost:807 validate -t TOKEN_FILE_NAME ```

TOKEN_FILE_NAME is the path of the file where the token is saved
