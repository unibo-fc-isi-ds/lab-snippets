# TCP Group Chat

A **TCP-based group chat application** that allows multiple clients to communicate via a server that broadcasts messages to all connected clients.

## Features
- **Group Chat**: Communication between all connected clients via a server.
- **Client Management**: The server handles client connections and disconnections.
- **Threaded Communication**: Both the server and clients use threading for simultaneous message sending and receiving.
- **Event Handling**: Events (like receiving a message or disconnections) are processed using callbacks.


## How to Test the tcp_group_chat app?
To start the server, use the following command. Replace <port> with the desired port number (es 8080).
```bash
poetry run python -m snippets.lab3.exercise_tcp_group_chat server <port>
```
Each client connects to the server by specifying the server's IP and port. 
Replace <server_ip> with the server’s IP address and <port> with the server's port number.
```bash
poetry run python -m snippets.lab3.exercise_tcp_group_chat client <server_ip>:<port>