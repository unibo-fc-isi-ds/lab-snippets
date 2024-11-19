# Exercise: TCP Group Chat

## Introduction

## Assumptions and limitations
- All the peers are connected with each other, making a full mesh topology
    - Not the best choice for scalability
- All usernames are unique
- All peers have already authenticated

## High Level Design
A peer-to-peer architecture has been chosen. Each peer is modeled as a TCPPeer, which consists of:
- a Server object: 
    - running on a specific port selected by the user
    - accepts connections from remote peers
    - creates a communication channel, i.e. a Client object, for each accepted connection
- a list of Client objects, i.e. the remote peers it is connected to: 
    - at launch time, the user specifies the list of endpoints (ip_address:port) of the remote peers

### Example
```
poetry run python -m snippets -l 3 -e tcp_group_chat 8080

poetry run python -m snippets -l 3 -e tcp_group_chat 8081 localhost:8080
poetry run python -m snippets -l 3 -e tcp_group_chat 8082 localhost:8080 localhost:8081
```

## Testing
The system has been tested in two distinct scenarios:
- **Scenario 1**: peers exchange messages with one another, and the goal is to ensure that all peers successfully receive the messages sent by others. 
To verify this, the messages transmitted are recorded in a log file. After the simulation, the content of the log is analyzed to confirm that it aligns with the expected behavior.
- **Scenario 2**: one peer disconnects from the network, and the objective is to verify that all other peers are notified about the disconnection. 
As in the first simulation, a log file is used to capture events during the process.

To run all the tests, you may exploit the following command:

```
poetry run poe test
```

Or simply run a specific test with:

```
poetry run python -m unittest discover -s tests -p "tcp_group_chat_simulation_1.py"

poetry run python -m unittest discover -s tests -p "tcp_group_chat_simulation_2.py"
```

The system has been tested on macOS, although Github Actions were used to ensure proper functionality on both Windows and Linux environments. 