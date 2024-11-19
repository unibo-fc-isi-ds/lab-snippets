# TCP Group Chat

In this exercise, i'll show my idea of a possible implementation of a Group Chat using TCP.

# Design and Implementation

I've developed a class called ```AsyncUser``` that contains aspects of both ```Server``` and ```Client``` class shown in the previous lectures.
Each ```AsyncUser``` contains data regarding his username, his socket, a set containing all its established connections with other chat users.



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

Another possible way to test the solution is by using run and debug feature of Visual Studio Code and selecting
from the list of options present in ```launch.json``` the followings in this specific order the first time we want
to activate it:
``` 
Test 1: Introduce First User
Test 2: Introduce Second User
Test 3: Introduce Third User
```

If one of the users is removed from the chat, they can be reintroduced using:
``` 
Test 4: first user exited and wants to re-enter
Test 5: second user exited and wants to re-enter
Test 6: third user exited and wants to re-enter
``` 