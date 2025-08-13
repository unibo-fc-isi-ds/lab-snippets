## General explanation

The objective was to make a TCP group chat where every peer acts as both a server and a client.

When a peer sends a message, it is broadcasted to all other peers he's connected to.

On startup, the peer starts listening for incoming connections on a specified port and eventually connects to other peers specified in the command line arguments, when a connection is established, the peer sends a message to the other one containing its name and everyone keeps a list of known peers and their names.

In order to avoid having a thread for each peer, the server listens for incoming connections and messages in a single thread and uses the `select` function to check for incoming messages and connections. The function is not used directly, but through the `select` method of the `selectors` module, which is a more user-friendly and high-level interface.

Every message is prefixed by the length of the message, which is a fixed size integer, and the payload is the message itself with a sender name and a timestamp.

Every connection, disconnection or name change is also notified in the console.

## Running

The server can be run with the following command in the repository root:

```bash
poetry run python .\snippets\lab3\exercise_tcp_group_chat.py <listen_port> [<peer1_ip> <peer1_port> ...]
```

You can change name once in the chat by typing 
```
/name <new_name>
```

You can exit the chat by typing
```
/exit
```

On exit no messages are sent to the other peers but since the system runs on TCP the connection is closed and the other peers will be notified of the disconnection.
