

# Peer to Peer Group Chat

# How it is designed
I've created the class ChatPeer, which encapsulates the logic of both the Client and Server classes. 

This class has two arrays of connections: 
- ```peer_to_write_to``` (Client Class): the connections actively established by the peer
- ``` peer_to_read_from``` (Server Class): the connections accepted, from other peers

These arrays are managed by the callback from last lecture. 
On new connection, the peer adds it to the array. 
When the connection is closed by the other peer, it is removed from both arrays.

When the Peer want to send a message, it iterates over the ```peer_to_write_to``` array, and send the message to every known and still active peer. 
Some debug prints warns when a new connection has been accepted or when a peer has left the chat. 

# How to Test
All the code is in the same file, including classes, functions and callbacks from previous lectures.
Everything can be tested manually using just the python command: 

```
python exercise_tcp_group_chat.py <username> <port> [peer1_ip:peer1_port] [peer2_ip:peer2_port]
```

For example, three peer can be launched like this, in different terminals: 

``` 
python exercise_tcp_group_chat.py user1 3000 127.0.0.1:3001 127.0.0.1:3002

python exercise_tcp_group_chat.py user2 3001 127.0.0.1:3000 127.0.0.1:3002

python exercise_tcp_group_chat.py user3 3002 127.0.0.1:3000 127.0.0.1:3001 
```

They will ready to chat with each other right after the sleep time (I've set 5 seconds as default, in order to have time to launch all three commands on different terminals.)
A peer can be disconnected from the chat by just hitting Ctrl-C or Ctrl-D.

Otherwise here is a script that automatically launch three peers as subprocesses, make them send a message and then leave the chat. When all subprocesses have terminated, it collects their stdout and stderr a prints to the main terminal.

```
python test_tcp_chat.py 
```