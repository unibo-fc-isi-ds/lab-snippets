TCP Group Chat through sockets and threads.
This single Python file allows the user to run the application in the role of server or client. 
When the user decides to run the server, he has to specify the reference IP address, to which the clients will have to connect, and also the port on which to start the socket.
When the user decides to run the client, he has to specify the IP address of the Server he wants to connect to, and also its port.
The Server runs a thread for each client, to handle its messages.
Every time a client send a message, it's sent in broadcast to all connected ones.
Every time a client closes the connection with the Server, all connected ones are notified and the system continues to work.

USAGE
python3 exercise_tcp_group_chat.py <server|client> <IP> <port>

CLIENT POSSIBLE ACTIONS
- join the group chat connecting to the Server
- choose a username
- type and send a message
- leave the group chat

REQUIREMENTS
- Python 3 or higher
- Python standard library to import "socket" and "threading" modules
- Windows, Linux or MacOS

TESTS
Some tests have been made:
- on the same machine with multiple consoles
- between two different VM (with different IP addresses) on the same network

CODE EXPLAINATION
main:
- if the user doesn't know he has to specify 3 arguments when he runs the application, it suggests him the correct usage 
- the first arguments represents the role of the system (server or client)
- the second one is the reference IP address
- the third one is the port
- if the user types an invalid role, the application returns error
- if everything's fine and "server" or "client" is the selected role, the program will call server_func() or client_func(), to execute the related correct operations

server_func():
It's a function that accepts an IP address and a port as arguments. It includes multiple sub-functions, such as:
- broadcast(), which tries to send a broadcast message to all connected clients, including the sender username and the message itself every time the server receives a new one. This try is inside a cycle that iterates all connected clients, but if one of them is unreachable (disconnected), the server removes it from the clients list
- handle_client(), which sends a welcome and a new join messages every time a new client connects to the Server. In add, it removed a client from the clients list if it's unreachable or it leaves the application, notifying all the others.
- in the end, the server has been configurated with a socket and it works through a cycle to handle the status of every client

client_func():
It's a function that accepts an IP address and a port as arguments. It includes multiple sub-functions, such as:
- receive_messages(), which tries to get all new messages from the buffer and print them
- send_messages(), which allows the user to choose a free username and, through a cycle, to type and send as many messages as he wants. If the user send "exit()" as message, its thread stops and the server (with handle_client() function) will detect the client as unreachable, removing it from the client list
- in the end, the client has been configurated with a socket and it works calling the two previous functions through a thread



 





