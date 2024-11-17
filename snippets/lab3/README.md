# Solution

The script creates a peer-to-peer group chat system using TCP connections. Each peer acts as both a server and a client.
Each peer maintains a list of known peers (client_list) represented by instances of the Client class.

When a connection closes, it is removed from the list to prevent sending messages to disconnected peers. On exiting the program, either due to a keyboard interrupt or EOF, all active connections and the server itself are gracefully shut down.


# Usage 
Follow these steps to launch a group chat with three peers: 

Open a terminal and start the first peer by running
```
poetry run python exercise_tcp_group_chat.py PORT_A
```
In a second terminal, start the second peer
```
poetry run python exercise_tcp_group_chat.py PORT_B IP_A:PORT_A
```
Finally, in a third terminal, start the third peer by running
```
poetry run python exercise_tcp_group_chat.py PORT_C IP_A:PORT_A IP_B:PORT_B
```

Users interact with the system by first entering a username and then typing messages in a infinite loop.