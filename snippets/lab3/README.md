Description
This project implements a simple peer-to-peer TCP group chat system using Python. Each peer acts as both a server and a client, allowing for messages to be broadcasted to all connected peers. The solution supports dynamic peer connections, where clients can join and leave the network at any time, similar to a UDP group chat.

Motivation and Choices
1.Peer-to-peer Architecture:
Using a decentralized design where every peer can act as a client and server simultaneously. It removes the reliance on a central server, making the system more fault-tolerant and flexible.
2.Multi-threading for Concurrent Connections:
Each incoming connection is handled in a separate thread, allowing the server to accept new connections without being blocked by ongoing communication.
3.Message Broadcasting:
Inspired by UDP group chat, the solution broadcasts messages to all connected peers to maintain a consistent message flow across the network.
4.Command-line Configurability:
Peers can be specified via command-line arguments, allowing for flexible network configurations and easy testing.

Testing
Functional Testing
1.Initial Setup: Start the first peer and verify it starts listening for connections.
2.Peer Connection: Start additional peers and connect them to the initial peer. Verify that connections are established.
3.Message Broadcasting: Send messages from any peer and observe that all connected peers receive the message.
4.Dynamic Joining/Leaving: Add new peers while the network is active and verify they can receive messages. Disconnect peers and ensure other peers continue functioning.
Edge Cases
1.Test with multiple peers connecting and disconnecting.
2.Test with large message sizes to ensure handling within the buffer limit.
3.Test network failure scenarios.
