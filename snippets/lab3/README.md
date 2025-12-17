# [A.Y. 2025/2026 Paradisi, Giovanni] Exercise: TCP Group Chat

The `exercise_tcp_group_chat` file implements a **group chat over TCP** using a combination of **Server** and **Client** class from the examples.
Each participant in the chat is represented by a **GroupPeer object**, which acts as both a server (accepting incoming connections) and a client (connecting to peers). In this way, every peer can communicate with multiple others, forming a distributed group chat network without a central server, 
so every clients may appear and disappear at any time without interrupt the communication of the other's member.

## Features
- Group chat over TCP where multiple peers can send and receive messages.
- Peers can join and leave at any time without interrupting the communication of others.
- Each peer broadcasts messages to all the peers it has been in contact with so far.

## How It Works

- Each participant is represented by a `GroupPeer` object.
- `GroupPeer` starts a TCP server that:
    - Listens on the given port.
    - Accepts incoming connections from other peers.
- At startup, a peer can optionally connect to a list of existing peers passed via command-line arguments.
- All active connections (both incoming and outgoing) are stored in an internal list of peers.

When the user types a message:

- The message is sent using the `broadcast` method to all connected peers.
- Each peer receives the message and displays it on its terminal.
- If a connection fails, the corresponding peer is removed from the list to keep the chat stable.

When the user types `/exit` or `Ctrl+C`:

- The peer sends an exit notification to all connected peers.
- Then it closes all connections and stops its local server.

## Usage
### **Copy and Run these commands in lab3 directory**
1. Start one peer with a chosen port:
```bash 
  poetry run python exercise_tcp_group_chat.py 8080
```
2. Start another peer and connect it to the first:

```bash 
  poetry run python  exercise_tcp_group_chat.py 8081 localhost:8080
```
3. Each instance will:
- Ask for a username.
- Print a “ready” message.
- Type messages that are broadcast to all connected peers.

Type `/exit` or `Ctrl+C` to leave the chat gracefully.
