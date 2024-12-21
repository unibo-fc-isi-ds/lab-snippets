# Exercise: RPC Auth Service

## Explanation

The solution extends the RPC infrastructure to support an authentication service. The main differences are:

- the `ServerStub` creates an instance of `InMemoryAuthenticationService` which has to do the actual authentication work;
- the creation of a `ClientStub` which manages the `AuthenticationService`;
- the presentation has been extended in order to manage (de)serialization of types as `datetime` and `timedelta`;
- the CLI has added the commands `authenticate` and `validate`, so the arguments `--tokenpath` and `--tokenduration`.

The command `authenticate` saves the token created in a JSON file that can be passed through the argument `--tokenpath` (the path starts from the home directory) or by default inside the file `token.json` in the home directory. In addition, the duration of the token by default is one day, but can be set via `--tokenduration` argument, specifying the number of hours.

The command `validate` retrieves the token in order to check his validity from the path, in the same way of the command `authenticate`.

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
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT get -u USER
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT check -u USER -p "PASSWORD"
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT check -u USER -p "WRONG PASSWORD"
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT authenticate -u USER -p "PASSWORD" [-t "PATH"] [-d DURATION]
$ python -m snippets -l 4 -e 4 SERVER_IP:PORT validate [-t "PATH"]
```
