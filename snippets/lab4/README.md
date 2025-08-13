# Description

The files present in snippets/lab4 were modified to implement both authentication and authorization of users.

### Request and serialization
- A dictionary field `metadata` was added to the `Request` dataclass
- Implemented serialization of datetime type in `Serializer` and `Deserializer` classes 

### ServerStub
- The `ServerStub` was extended with a `InMemoryAuthenticationService` that will handle the requests of authentication and validation from a client
- The `ServerStub` now can be initialized with a list of users. This list is necessary to perform operations on the server, as adding other users now requires authentication. In this case a single admin user is passed to the server
- The `__handle_request` method has been modified so that only requests which contain a valid token can perform actions on the database. This means that when starting the server there must be already at least one user registered. 
- The method `__is_authorized` has been implemented to determine if a request can be fulfilled based on the role of the user making the request. Only admins can use the `get` and `check` methods and new admin users can only be added by other admins

### ClientStub
- The `ClientStub` now has a `token` field which will be set to **None** if the user has not yet authenticated. This field will be used in the `metadata` field of every new `Request`
- The methods `store_token` and  `get_token` were implemented
- A new class `RemoteAuthenticationService` which extends the `ClientStub` was implemented to perform authentication and validation requests

### Command Line
- A new flag `--token` was added. It has to be used in case the user wants to specify the path were the token will be saved and/or retrieved at each execution. If no path is provided then the default location will be used
- The following commands were added:
    1) **authenticate**: if the credentials are correct, stores the returned token inside the `RemoteUserDatabase` and the `RemoteAuthenticationService`.
    Since these are recreated at each execution, the token is also saved to a file
    2) **validate**: checks if the specified token is still valid
    3) **delete_token**: which deletes the specified token, so that no other user will be able to use it

# How to test

To get started, **you must first start the server**

```
python -m snippets -l 4 -e 2 server_port
```

Running any command before authenticating will now return an error, so initially the user must use the command `authenticate` as follows:

```
python -m snippets -l 4 -e 4 server_address:server_port authenticate -u username -p password
```
It's also possible to use the email address instead of the username.

The commands `validate` and `delete_token` can be used as follows

```
python -m snippets -l 4 -e 4 server_address:server_port validate

python -m snippets -l 4 -e 4 server_address:server_port delete_token
```

The flag `--token` or `-t` can be used to specify where the token should be saved when using the `authenticate`. In this case the user has to specify the token path every time they execute any other command.

For example, if a user authenticates by specifying a token path and then wants to execute the `get` command, they should do as follows:

```
python -m snippets -l 4 -e 4 server_address:server_port authenticate -u username -p password -t token_path

python -m snippets -l 4 -e 4 server_address:server_port check -u username -t token_path
```


As mentioned earlier, initially the only registered user on the server is the admin, so to perform any actions you must authenticate using the following credentials.
- username: admin
- emails: admin@mail.com
- full_name: Admin
- role: ADMIN
- password: qwerty1234 