# Description

Every peer works as a server and as a client at the same time, which means that:
- At any time it can accept incoming connection from other peers
- Handles incoming messages and shows them to the user
- Can send messages to other peers

A user can create a new TCP group chat by running the script without specifying addresses of other peers.
When a user wants to join an existing group chat they must specify at least another peer, which, if they connected successfully, will provide the list of all the other peers present in the group chat.

A user can provide multiple peers to connect to, so that if the first of them isn't reachable the user tries to connect to one of the others, until it manages to connect. If no connection is successful then a new group chat is created.
If a user provides addresses of peers that are in different group chats, they will join the one to which they manage to connect first.  

To simplify sharing the address of a peer already present in a group chat with another user, the local IP address is displayed on the screen when the user creates or joins a group chat.

When a new user joins a group chat the following steps take place:
1) The user has connected to one of the peers of the group chat, so they request to know the other peers present
2) The peer receives the request and sends a list containg the addresses and names of the other peers as a response
3) The user tries to connect to each of the peers and, if successful, sends a 'greeting' message to let them know that they joined.
4) The peers receive the 'greeting' message, which prints '{User} has joined the chat'
5) Finally the user is able to send and receive messages

The messages sent in the group chat have a json structure to better handle the different informations contained inside every message.

A user has multiple ways to disconnect from a group chat:
- typing 'exit': disconnects the user gracefully, which means that they will send a message to every peer to let them know that they are disconnecting.
- pressing Ctrl+C: same as 'exit'
- closing the terminal: the user doesn't send a 'disconnect' message, so each peer realises that the connection has been lost

# How to test

The script can be tested by running one of the following commands:

- Create a new group chat:
poetry run python snippets/lab3/exercise_tcp_group_chat.py port

- Try to join an already existing group chat:
poetry run python snippets/lab3/exercise_tcp_group_chat.py port address_1:port_1 ... address_n:port_n

Also in launch.json some configurations with prefix 'Ex' have been added.

Once the scripts are running try sending messages!
