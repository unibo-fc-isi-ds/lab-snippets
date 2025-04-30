
# TCP Group Chat 

The file "exercise_tcp_group_chat.py" contains a proposed solution to the “TCP Group Chat” assignment. The goal was to implement a TCP-based group chat that could also handle abnormal situations, such as network partitioning or disconnections. 

### Description of the solution

The proposed solution has two main classes: “Peer” which represents the class that internalizes the client and server concepts and “Controller” which contains the application logic that interfaces with the user. One of the main goals of this solution is to make a “Peer” class that can also be reused for functions other than TCP Group Chat.

The main challenge was, unlike UDP-based group chat, managing multiple persistent connections. 

I decided to use a single socket as far as the server side was concerned, with the ability to accommodate up to a set number of connections; however, it was necessary to create a thread in order to handle socket listening for each connection. This allowed only one port to be used as a reference, but to be able to handle multiple connections. On the client side I chose to create a socket for each outgoing connection, maintained in the peer class. 

To merge the concepts of client and server, to create a connection, one Peer creates an outgoing connection to another Peer's port and establishes the connection, also communicating the coordinates for the reverse connection; so that the other peer can proceed in the same way, creating a two-way connection. 

At the end of the connection, a Peer sends a signal to the connected Peers alerting them to disconnect from the network.

The messages have been encoded in JSON, so that there is a fair amount of expandability to multiple uses.

To ensure a good quality of the produced solution, tests were carried out with Pytest, both for the main functions and for Peers. For some functions, such as IP address validation, a Fuzzing library was chosen: “hypothesis”, to test the functions with as many inputs as possible. I tried to make peer tests as deterministic as possible.

### Usage
First, it is important to proceed with the steps described by the main README. Then, to use the “hypothesis” fuzzing library, it is necessary to import it into the poetry environment. The dependency has already been added to the “pyproject.toml” file, so you just need to give the command:
```
poetry update
```
In order to use the test functions, it is necessary to give the command (it may take a while):
```
poetry run pytest exercise_tcp_group_chat.py
```
In order to use the application, it is necessary to specify as arguments:

- Ipv4 address of the network card we are going to use
- Port that we are going to use
- A list of ip addresses with the corresponding ports we want to connect to (**x.x.x.x:port** format)
For example, if we want to create a first peer in the 8080 port:
```
poetry run python3 exercise_tcp_group_chat.py localhost 8080
```
For a second Peer that will connect to the first peer:
```
poetry run python3 exercise_tcp_group_chat.py localhost 8081 localhost:8080
```
ad so on.

Please note that if we use references such as "localhost" or "127.0.0.1" it will not be possible to connect to other devices on the local network; In that case you must specify the local IP address as "192.168.1.50".