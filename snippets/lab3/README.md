# TCP Group Chat
The proposed implementation considers each peer to be both a client and a server. Each peer creates a server instance, and any other peer already known must be written to the command line to be added as a client of the former.
When a peer sends a message it notifies every client it has added to its set, when it leaves the chat it notifies every client in its set by closing the connection and then it closes the server.

# Testing
The project can be tested by manually running each peer in a different terminal using `poetry run python -m snippets.lab3.exercise_tcp_group_chat <port> [<ip1>:<port1> <ip2>:<port2> ... <ipN>:<portN>]`.

Alternatively, a simple test is implemented using different threads to try out the architecture. At the top of the code you can specify the initial port, the number of peers to create and the list of phrases to be used by them. Note that in the current implementation, the number of messages written by each peer before it's disconnected is chosen randomly. The test can be run with the following command `poetry run python -m snippets.lab3.test`.
