In this implementation, each peer functions as both server and client. A set of peers is used to manage connections with multiple peers.
At startup, this set is initialized, using the endpoints specified through command-line arguments, allowing the peer to immediately connect to others. Additional peers are dynamically added to the set, as new users connects.
Messages are broadcast to all peers in the set, ensuring seamless communication across the network. When a peer disconnects, it is promptly removed from the set, and an appropriate EXIT_MESSAGE message is sent. Upon encountering an `EOFError` or `KeyboardInterrupt`, the script ensures a graceful shutdown by terminating all active connections with the remote peers and closing the server.

It it possibile to start the program either with a single peer, specifying only the port as a parameter, or as a peer that needs to connect to other peers, adding their respective endpoints. Different code for common functionalities is taken from previous lectures.

Startup command example with all parameters:
poetry run python -m snippets.lab3.exercise_tcp_group_chat PORT PEER1_IP:PEER1_PORT, ..., PEERn_IP:PEERn_PORT

Example with 3 users:
poetry run python -m snippets.lab3.exercise_tcp_group_chat 8080
poetry run python -m snippets.lab3.exercise_tcp_group_chat 8081 localhost:8080
poetry run python -m snippets.lab3.exercise_tcp_group_chat 8082 localhost:8080 localhost:8081