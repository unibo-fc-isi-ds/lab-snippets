New Feature:

Broadcasting Messages:

Developed a broadcast_message method that helps in sending messages to all the clients connected except the sender. This function helps in the interactivity of chat applications since it allows the sender of a message to everyone that is camping the group.

Connection Management:

In the interests of receiving messages and also dealing with the connection and disconnection events, the functions which were added include the on_message_received and on_new_connection:

on_message_received deals with the messages in the clients which are sent to other clients and manages disconnection if it happened.

on_new_connection deals with the new clients who have joined the chat room and adds them to connected_clients increasing the number of people connected to the chat.

Client Disconnecting Feature:

In case a user wants to leave the chat he/she has the option to disconnect, and the server will know that the user has disconnected. This feature aids in the letting of the chat application for many users entering and leaving sessions.

How to Test The Solution:

1-Start the Server:

To run the server, execute the command:

python exercise_tcp_group_chat.py server <PORT>

2-Run Client(s):

For every other client intending to connect to the chat, open another client with the command below:

python exercise_tcp_group_chat.py client <SERVER_IP> <PORT>
