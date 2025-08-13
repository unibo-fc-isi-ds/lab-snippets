This project is designed to solve the problem of real-time group communication over TCP using a decentralized peer-to-peer chat model. This implementation allows all peers to act simultaneously as both clients and servers, where each peer in the network broadcasts messages to all other peers it has been in contact with, creating a fully connected chat network.
It uses a set of classes (Server, Client, and Connection) to manage connections, message broadcasting, and error handling. The Connection class handles the underlying socket operations, ensuring messages are sent and received in a structured manner. The Client class inherits from Connection and manages outgoing communications, while the Server class accepts incoming connections and handles events such as new connections, disconnections, and message broadcasts.
There is a global variable 'peers' that holds a set of Client objects, representing all the peers currently connected. This allows for a more complex peer-to-peer network where each peer can send messages to all other peers it has connected with. The message broadcasting is handled by the broadcast_message function, which sends the message to all peers in the peers set, and it also removes peers from the set when their connection is closed.

Usage: 
To use the project, start a peer with poetry run python -m snippets.lab3.exercise_tcp_group_chat PORT.
The peer will prompt for a username to join the chat.
Users can type messages, which will be broadcasted to all connected peers.
The script handles incoming messages from other peers and displays them in the chat.
To start a peer in the network, use the command:
    peer1: poetry run python -m snippets.lab3.exercise_tcp_group_chat PORT_A
    peer2: poetry run python -m snippets.lab3.exercise_tcp_group_chat PORT_B IP_A:PORT_A
    peer3: poetry run python -m snippets.lab3.exercise_tcp_group_chat PORT_C IP_B:PORT_B IP_A:PORT_A

