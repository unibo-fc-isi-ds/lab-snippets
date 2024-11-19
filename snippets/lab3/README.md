# TCP Group Chat

In this exercise, i'll show my idea of a possible implementation of a Group Chat using TCP.

# Design and Implementation

I've developed a class called ```AsyncUser``` that contains aspects of both ```Server``` and ```Client``` class shown in the previous lectures.
Each ```AsyncUser``` contains data regarding his username, his socket, a set containing all its established connections with other chat users and a ```bool``` flag to check whether or not the user is active.

```AsyncUser``` contains both ```def start_connection``` in order to start the connection with other peers that are currently in the group chat, and ```__handle_incoming_connections``` which lets each member of the chat to listen and accepts new connections with new peers that have entered the chat (adding them in their set ```remote_peers_connections```). Each new connection receives ```__handle_peer_message``` as their callback to handle new messages received by other peers. Each time a peer sends a new message, it is encoded inside ```def send_message``` and then sent to each other member them with  ```def broadcast_message```, that uses saved set of connections of that user to send a message to each connected peer. Once a peer decides to leave the chat (either by inputting ```/quit``` in the terminal or by generating a ```KeyboardInterrupt``` Exception with CTRL+C), method ```def close``` sends a final broadcast message to signal each other peer that the user is leaving the chat, then finally removing each peer from the set with ```def remove_peer``` (it closes each connection the leaving peer has) and finally closing the socket of the leaving peer.

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

When one of the user leaves, the others will continue chatting. If a peer exists and wants to re-enter, they must be launched from terminal putting ```IP:PORT``` of each remaining peer in the chat.

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