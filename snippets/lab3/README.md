Description
This project implements a simple chat application that supports multiple clients connecting to a single server. 
The solution uses Python's socket module for network communication and threading for handling concurrent connections.

Features
The server can handle multiple clients simultaneously.
Clients can send messages to the server, which broadcasts them to all connected clients.
A simple protocol ensures that each message is prefixed by the username of the sender.
Clean disconnection for clients:
Clients can exit by typing exit or quit.

Motivations
Concurrency with Threads:

Threads were chosen for their simplicity in handling I/O-bound tasks such as managing multiple client connections.
Python's threading module provides an intuitive way to manage separate tasks for listening to client messages and broadcasting them.

Socket Communication:

The socket module was chosen for its flexibility and direct control over TCP communication.
Using TCP ensures reliable message delivery between server and clients.

Ease of Use:

The application is designed to be simple to deploy and run.
Clear instructions and intuitive commands (exit/quit) make it accessible for users with minimal technical expertise.


Testing the Solution:

Pre-Requisites:
Install Python 3.7 or later.
Ensure all files are in the snippet/lab3 directory.

How to Test:
1) Open a terminal and navigate to the snippet/lab3 directory.

2) Start the server:

python chat.py server <port>
Replace <port> with a valid port number

3) Open multiple terminals and connect clients:

python chat.py client <host>:<port>
Replace <host> with the server's IP (e.g., 127.0.0.1 for localhost) and <port> with the port used by the server.

4)Each client will be prompted to enter a username. After providing a username, clients can send messages by typing them and pressing Enter.

5)Test message broadcasting:

Send messages from one client and verify that all other clients receive them.

6)Test disconnection:

Disconnect a client by typing exit or quit. Observe the message indicating the client has left.

Usage Notes
The server must always start first to accept incoming client connections.
Use unique usernames to avoid confusion.
If a client disconnects abruptly, the server will handle the cleanup and continue running.

File structure

Each snippet consist of a Python module, which is a file with a `.py` extension.
Snippets paths and names are organized as follows:

snippet/lab3/
├── exercise_tcp_group_chat.py         # The main script for both server and client
├── README.md                          # Documentation for the chat application
├── Example1_tcp_echo_wrong.py
├── Example2_tcp_echo.py 
├── Example3_tcp_chat.py 

