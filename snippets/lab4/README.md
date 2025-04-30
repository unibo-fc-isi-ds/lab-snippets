This implementation adds support for *authentication* and *authorization*.  

## Added commands
 - `auth -u user -p pass`
 - `validate -u user (after auth)`

## Authentication
User authentication is handled by saving the generated tokens locally, which will be sent in the metadata field for requests that need them. The requests were then modified to support this new data and send it automatically for operations that are protected.

## Protected access
Calling protected methods, like `get`, the credentials are checked for validity, the same for the token and finally the role of the user. If each piece of data matches and you have the right permissions the required information about the user is returned.

Thus, the serialization/deserialization of data, the format of requests, and the handling of `__handle_request` in the ServerStub were modified. In the ClientStub, `RemoteUserAuth` was added for handling protected commands and managing permissions. Finally, the Client CLI was modified to support the behaviors we have described.

## Usage examples
The commands already present remain fully supported.

Wanting to test the system, you initially proceed by starting the server:

    python -m snippets -l 4 -e 2 8080

Then some commands, such as the one for adding a user, can be executed:

    python -m snippets -l 4 -e 4 localhost:8080 add -u pier -a pier@gmail.com -n "Pier Costante Babini" -r admin -p "pass"
Following the addition of at least one user, it is possible to authenticate, for example, using the credentials just added:

    python -m snippets -l 4 -e 4 localhost:8080 auth -u pier -p pass
A token, saved locally, will then be generated for the authenticated user.
You can check the validity of the token with the command:

    python -m snippets -l 4 -e 4 localhost:8080 validate -u pier
Finally, certain operations, such as the `get`, can be protected so that they are only executable to admins:

    python -m snippets -l 4 -e 4 localhost:8080 get -u user --auth-user pier --auth-password pass
In this case, `user` data are selected using `pier` and `pass` as credentials.