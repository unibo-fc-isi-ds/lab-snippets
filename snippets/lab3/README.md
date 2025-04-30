
### Architecture

Each peer operates as a decentralized entity with two primary capabilities:
1. Communicating with other peers via application messages.
2. Optionally, providing its own information to peers upon request.

<br>

The main goal is to enable the creation of a **seed/bootstrap peer** with an additional protocol capability to:
- Serve as an entry point for the group chat, allowing discovery of current peers.
- Manage the consistency of the group chat with some limitations (see the **Consistency** section).
- Facilitate fault tolerance by avoiding a single point of failure (see the **Fault Tolerance** section). In theory, every new user joining the group chat could also serve as a bootstrap peer, achieving full decentralization.

**Note:** While having all peers act as bootstrap peers might seem advantageous, it also introduces complexity. Beyond the process for incoming application connections (via a welcoming socket), an additional process for incoming bootstrap initialization connections (via a bootstrap socket) will also be required.

<br>
A new peer seeking to join does not need the complete list of peer addresses; it only needs the address of one bootstrap peer.
<br>

When contacted, the bootstrap peer sends all the information it has about the chat (represented as a list of tuples: `(username, target_welcoming_address)`). Using this information, the new peer will attempt to establish connections with all listed peers.
- To simplify this approach, each new connection is configured with the provided information.
<br>
The bootstrap protocol is fully independent of the messaging protocol:
- Both protocols include their own callbacks for handling events.
<br>

In the messaging phase each peers broadcast its own message to the other peers wich he has connections with:
- every peer is responsable to monitor (and remove) the connection through a separate thread
- to improve efficiency every peer will also try to connect to others through different threads (when the connection is achieved the thread will join the parent thread)
<br>

---

### Bootstrap vs. Standard Peer

From a practical perspective, the primary difference between a bootstrap peer and a standard peer lies in the bootstrap peer's ability to handle requests for peer information (e.g., the welcoming socket details of other peers).

**General trade-offs:**
- **More bootstrap peers**: Greater decentralization.
- **More standard peers**: Lower individual computational cost (since they do not need to accept and respond to peer information requests).
<br>
As long as the group chat includes at least one bootstrap peer, different peer configurations can be used.
<br>
**Fully Decentralized:**
- **N bootstrap peers**
- Each peer is configured with the bootstrap addresses of other peers, minimizing the risk of network partitioning.
<br>
**Client-Server Model:**
- **1 bootstrap peer, N-1 standard peers**
- This model introduces a single point of failure but ensures strong consistency, as only one peer needs to handle requests and maintain the peer state.
<br>
**Hybrid Model:**
- **N-M bootstrap peers, M standard peers**
- This approach avoids a single point of failure while offering greater flexibility. Each peer can connect to multiple bootstrap peers, enhancing redundancy.
<br>
---

### Testing

```bash
poetry run exercise-chat --mode <M> --w_port <W> --b_port <B> --remote_endpoint <R>
```

where

- `<M>` can be `standard` or `bootstrap`
- `<W>` is the welcoming socket port to listen for new connections
- `<B>` is the bootstrap socket port to listen for peer retrieval (only in `bootstrap` mode)
- `<R>` the remote address (of a bootstrap peer) where to retrieve peers (optional)

##### Example: Fully decentralized newtork with 3 peers
- the third command could also be runned with `localhost:8082` (both are bootstrap peers)
```bash
poetry run exercise-chat --mode bootstrap --w_port 8081 --b_port 8080 

poetry run exercise-chat --mode bootstrap --w_port 8083 --b_port 8082 --remote_endpoint localhost:8080

poetry run exercise-chat --mode bootstrap --w_port 8085 --b_port 8084 --remote_endpoint localhost:8080
```

##### Example: Client-Server with 3 peers
- the first peer is the single point of centralization, in case of failure the network would be completely partitioned
```bash
poetry run exercise-chat --mode bootstrap --w_port 8081 --b_port 8080 

poetry run exercise-chat --mode standard --w_port 8083 --remote_endpoint localhost:8080

poetry run exercise-chat --mode standard --w_port 8085 --remote_endpoint localhost:8080
```

---

### Consistency

If a peer fails to connect to even one target welcoming address within a specified timeout, it will automatically shut down.
- A user unable to establish all connections will not be able to send messages.

On the other hand, if the peer successfully connects to all targets, it officially becomes part of the chat and can begin broadcasting messages to all other participants.

Without centralization (neither a server nor an election system), **strong consistency cannot be guaranteed**. For instance, one peer might learn about a new connection before others, leading to temporary inconsistencies. However, the group chat's state will eventually reach consistency across all peers.

**Potential Improvements:**
- **Eventual Consistency:** Without centralization or an election system, connection states across peers may experience brief inconsistencies. However, thanks to the timeout mechanism, each peer's state will always converge to eventual consistency.
- **Bootstrap Peer Synchronization:** If bootstrap peers synchronized their updated connection states before responding to new peers, greater consistency could be achieved. However, this might reduce availability.

---

### Fault Tolerance

Peers are fully independent and unaffected by the failure of others. In the event of a socket disconnection, peers automatically remove the faulty connection data from their state.
- Every message connection is interrupted if one of the two peers exits or encounters a fault.

**Handling a Fault Scenario:**
1. Two bootstrap peers, A and B, are connected.
2. Peer C contacts A via its bootstrap socket. A responds with the list of peers.
3. Before C can connect to the peers listed by A, peer B disconnects.
4. C successfully connects to A.
5. C attempts to connect to B but times out.
6. C disconnects from the group.

This approach treats future inconsistency problems as faults and attempts to handle them gracefully.

**Possible Improvements:**
- **Retry Mechanism:** Instead of disconnecting after a single timeout, multiple connection attempts could be made before giving up.
- **AFK Timeout Check:** Currently, peers can remain indefinitely connected without interacting. Introducing a timeout for long periods of inactivity could improve resource management.

