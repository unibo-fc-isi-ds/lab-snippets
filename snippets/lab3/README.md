This script implements a peer-to-peer TCP-based group chat application. Each peer can act as both a server and a client, allowing users to join and interact with the others.
A set of peers is used to manage connections with multiple peers. In the beggining, the set is initialized, peers connect to other users specified via command-line arguments. New peers can dynamically join the network that means when starting a new peer, the user specifies the addresses of one or more existing peers in the network (endpoints) once connected, the new peer becomes part of the network, and it starts listening for incoming connections from other peers as well.
Messages sent by a user are broadcast to all connected peers. When a peer disconnects, it is safely removed from the network and an EXIT_MESSAGE is broadcast to inform other users. The application ensures clean termination when interrupted (EOFError or KeyboardInterrupt), closing all active connections and shutting down the server.
The program can be launched in two ways: either as a standalone peer by specifying only the port number, or as a peer that joins an existing network by providing the endpoints of other peers to connect to.

Command for testing with all parameters:
poetry run python -m snippets.lab3.exercise_tcp_group_chat.py PORT PEER1_IP:PEER1_PORT, ..., PEERn_IP:PEERn_PORT

Example with 3 users:
poetry run python -m snippets.lab3.exercise_tcp_group_chat.py 8080
poetry run python -m snippets.lab3.exercise_tcp_group_chat.py 8081 localhost:8080
poetry run python -m snippets.lab3.exercise_tcp_group_chat.py 8082 localhost:8080 localhost:8081