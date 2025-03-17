# go-chat-tcp-p2p: Peer-to-Peer Group Chat

go-chat-tcp-p2p is a simple peer-to-peer group chat system, implemented using TCP sockets, that allows users to connect to chat groups by knowing the port of a peer already in the group. 

## Usage Guide

To use this group chat system, follow these steps:

### 1. Clone the Repository

First, clone the repository to your local machine by running:
```bash
git clone [<repository-url>](https://github.com/ferriforty/go-chat-tcp-p2p)
```
### 2. Navigate to the Project Folder

After cloning the repository, navigate to the project folder:
```bash
cd go-chat-tcp-p2p
```
### 3. Start Your Peer

If you want to create your own new group-chat just run the main.go file and specify the port you want to use. It will default to localhost:
```bash
go run main.go <your-port>
```
This will create your own peer on the specified port.
And you will need to wait to someone to join you to start chatting, keep waiting i assure you someone will want to talk to you 😘 (Probably just yourself 💀)
### 4. Join a Group Chat

To join a group chat, you need the port number of a peer that is already part of the chat group (Most of the times yourself in another terminal 😭). You only need one peer’s port to connect to the group.

Once you have the peer’s port, run your peer with both your own port and the peer’s port as parameters:
```bash
go run main.go <your-port> <peer-port>
```
### 5. Enjoy the Chat

Once you connect, everyone else will be notified that you've joined the group chat. You will also receive the complete chat history up to that point. From there, you can start chatting with other members of the group!
Have fun 😆
