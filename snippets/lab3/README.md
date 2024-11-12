# TCP_group_chat designed by Jing Yang
The core feature of this application is the **group chat** functionality, allowing clients to communicate with all other connected clients via a server that handles message broadcasting.

#### Server-Side Group Chat Design
- **Broadcast Mechanism**: The server maintains a list of active clients, adding new connections to this list when clients connect. Each message from a client is broadcast to every other client in the list, except for the sender.
- **Client Management**: When clients disconnect, the server removes them from the active connection list, ensuring that messages are only sent to currently connected clients. This prevents issues related to sending data to closed connections and helps manage resources effectively.
- **Threaded Communication**: The server operates a separate thread for each connected client. This threaded approach allows the server to handle multiple clients concurrently, preventing one client's messaging or disconnection from blocking others. 

#### Client-Side Group Chat Design
- **Simultaneous Send and Receive**: Each client also uses threading to enable simultaneous sending and receiving of messages. This design ensures that a client can display incoming messages from other clients while still allowing users to type and send new messages without interruption.
- **Event-Based Handling**: Both server and clients use callbacks to handle events (such as receiving a message, connection errors, or disconnections). This structure simplifies extending functionality, as different types of events can be processed independently without affecting the main loop.
- **Endpoint Initialization**: Each client, at launch, can be informed of other peer endpoints, making it flexible to introduce additional functionality, such as direct messaging between clients if required.

## How to Test the tcp_group_chat app?
- **Manual Test**: 
To start the server, use the following command. Replace <port> with the desired port number (e.g., 8081).
```bash
poetry run python -m snippets.lab3.exercise_tcp_group_chat server <port>
```
Each client connects to the server by specifying the server's IP and port.Replace <server_ip> with the server’s IP address (e.g., 127.0.0.1) and <port> with the server's port number.
```bash
poetry run python -m snippets.lab3.exercise_tcp_group_chat client <server_ip>:<port>
```
- **Automatic Test**: 
```bash
poetry run python -m snippets.lab3.test_run
```
In this test srcipt by python, I designed a server and 3 clients named 'jing yang''mobius''YJ', and simulate client behaviour. 
Also created extrem situation that someone unexpectedly leave the chat group.