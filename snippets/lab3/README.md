# TCP Group Chat

The solution proposed aims to let every peer acts both as a server and as a client. For each peer there is an instance of a server in order to accept new connections and so a set of `remote_peers` is used to manage the interaction between multiple peers. This set is populated immediately with all the client endpoints specified via command line arguments, and then other peers can be added when users connects to the local endpoint. When a message is sent by a peer, it is forwarded to every peer in the `remote_peers` set. When a peer disconnects, it's removed from the set and a notification message is sent to all other peers. In case of an `EOFError` or `KeyboardInterrupt` the script is gracefully terminated by closing the server and so the connections with all the remote peers, also sending them a notification message.

# Testing
The project can be tested by manually running each peer in a different terminal using:

`poetry run python -m snippets.lab3.exercise_tcp_group_chat <port> <address2>:<port1> <address2>:<port2> ... <addressN>:<portN>`.

The list of pair `<address>:<port>` represents the peers already connected to the chat and that will be added to the `remote_peers` set at the start.