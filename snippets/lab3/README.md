# Solution

The program creates a peer-to-peer tcp group chat. Each peer is both a server and a client.
Each peer have a set of peers (client_list) which are represented by instances of the Client class.

When close a connection, the nodes from set are closed one by one to prevent sending messages to disconnected peers. On exiting the program, with a keyboard interrupt or EOF, 
all connections and the server will be shut down.


# Case use 
There are steps to launch a group chat with three peers: 

Open a terminal and start the first peer by running
```
poetry run python exercise_tcp_group_chat.py PORT_A
```
Then in a second terminal, start the second peer
```
poetry run python exercise_tcp_group_chat.py PORT_B IP_A:PORT_A
```
Finally, in a third terminal, start the third peer by running
```
poetry run python exercise_tcp_group_chat.py PORT_C IP_A:PORT_A IP_B:PORT_B
