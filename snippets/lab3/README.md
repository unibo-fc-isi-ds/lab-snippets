# P2P Group Chat

Creating a p2p group chat where each peer forwards a message to all other peers.

The peers connected to another peer are specified manually as parameters.

Each peer is assigned to a port, along with the IP addresses and port numbers of the other peers with the address:port notation.

To run the program use:

poetry run python .\snippets\lab3\exercise_tcp_group_chat.py port_number ip_address:port_number of each peer you want to connect to
