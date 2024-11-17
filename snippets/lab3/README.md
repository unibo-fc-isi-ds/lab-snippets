# TCP Group Chat

In this exercise, i'll show my idea of a possible implementation of a Group Chat using TCP.

# Design and Implementation



# Testing
The code for design's implementation is all in the same file, including classes, functions and callbacks shown in
previous lectures as examples.

The group chat can be tested manually using terminals and the command:
```
poetry run python -m snippets -l 4 -e 4 <port> <username> [peer1_ip:peer1_port]
```

Here is an example of three peers launched, each line in a different terminal:

``` 
poetry run python -m snippets -l 4 -e 4 8080 Andrea
poetry run python -m snippets -l 4 -e 4 8081 Giovanni localhost:8080
poetry run python -m snippets -l 4 -e 4 8082 Francesco localhost:8080 localhost:8081
```