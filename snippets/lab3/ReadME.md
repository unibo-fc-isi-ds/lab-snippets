This solution incorporates the Client-Server architecture from the example, but the server takes also the role of broadcasting to every other peer who connects to the chat.
It's prone to many faults such as:
- The server not broadcasting a user's disconnecting
- When the server goes down, the chat no longer functions

Some solutions come to mind to fix these issues, such as implementing some logic such that when the server does go down, some other user takes up its role as the broadcaster.
In future versions these issues will be addressed.
