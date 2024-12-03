# Exercise: RPC Auth Service 2

## Explanation

The solution extends the RPC infrastructure to support an authorization service. The main difference is that the `get_user` operation requires authentication and authorization, so it should only be possible for authenticated users whose role is admin.

The implementation of the authorization follows these steps:

- the `Request` has been extended with the optional field `metadata`, which for now can only be filled with the token;
- when the user wants to retrieve the data, the request's metadata is filled with the token of the user;
- the `ServerStub` is extended in order to check that the user has the authorization to make that request (for now only `get_user`). The role of the user, the presence and validity of the token are checked;
- the `ClientStub` is extended to fill the metadata field of the request with the token every time after the first time.

The command `authenticate` saves the token created in a JSON file that can be passed through the argument `--tokenpath` (the path starts from the home directory) or by default inside the file `USERNAME.json` in the home directory, in order to have the possibility to save multiple tokens, meanwhile in the first exercise the default path was `token.json`.
The same path's logic is used in case of `get` command in order to retrieve the token.

## Testing

The solution can be tested via CLI, using two different terminals:

- the first one acts as the server, so it has to run the following command:
```
python -m snippets -l 4 -e 2 PORT
```

- the second one has to act as a client, so it's possible to use every available command which are `add`, `get`, `check`, `authenticate` and `validate`.
In order to test properly the service, the following one is a reasonable sequence of commands:
```
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT add -u USER -a EMAIL1 [EMAIL2] -n "FULLNAME" -p "PASSWORD" [-r ROLE]
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT get -u USER [-t "PATH"]
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT check -u USER -p "PASSWORD"
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT check -u USER -p "WRONG PASSWORD"
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT authenticate -u USER -p "PASSWORD" [-t "PATH"] [-d DURATION]
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT validate [-t "PATH"]
```
