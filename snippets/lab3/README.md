# tcp group chat
This project provides an implementation of a tcp group chat. Each peer acts both as a server, listening for connection requests, and as a client, initiating connections to other peers. A peer can only connect to other peers that are already running. In order to connect to a peer, you need to know its ip address and tcp port.

## How to run:
In order to run a peer

    poetry run python -m exercise_tcp_group_chat <port> [<ip:port> ...]

where:
* <port>: is the the port of the peer
* <ip:port>: is the ip address and tcp port of the peer you want to connect to

### Example:

    poetry run python -m exercise_tcp_group_chat 16000

    poetry run python -m exercise_tcp_group_chat 16001 192.168.1.9:16000

    poetry run python -m exercise_tcp_group_chat 16002 192.168.1.9:16001 192.168.1.9:16002
