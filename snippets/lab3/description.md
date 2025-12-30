# [A.Y. 2025/2026 Zhabagin, Rakymzhan] Exercise: TCP Group Chat

## Overview - what I added

This PR adds `snippets/lab3/exercise_tcp_group_chat.py`: a TCP *peer-to-peer* group-chat example where each process acts simultaneously as server and client. Peers can be started with a (possibly empty) list of initial peers; they accept incoming connections and remember any peer they talk to, then broadcast locally-originated chat messages to all remembered peers.

**Key behaviors:**

* JSON-encoded chat payloads (see format below).
* Self-detection via a UUID `sender_id` so locally-sent messages print as `You:` when the sender receives/echoes them back.
* Thread-safe connection registry (incoming + outgoing).
* Graceful idempotent shutdown (Ctrl+C or `/quit`).
* Reuses the existing `Server`/`Client`/`Connection` and helper functions exported by `snippets.lab3` (e.g. `address()`, `local_ips()`, `message()`).

---

## Why this design (motivation & choices)

* **Reuse existing socket abstractions.** The low-level framing and event model (length-prefixed messages, `Connection` threads, `Server`/`Client`) were already implemented in the repository - reusing them keeps the new code concise and avoids duplicating socket logic.
* **Peer-as-both-server-and-client model.** The assignment asks for TCP group chat with dynamic join/leave semantics resembling the UDP example: making every node both server and client supports peers appearing/disappearing and mirrors the expected behavior.
* **JSON payloads.** They are easy to parse/debug and extensible for future fields (e.g., message IDs, peer lists).
* **UUID `sender_id`.** Using a stable, process-unique ID prevents mislabeling messages when there are multiple connections (A->B and B->A). It also makes local echo detection robust.
* **Thread-safety.** A `threading.Lock()` protects the shared connections map because multiple connection threads may add/remove connections concurrently.
* **Idempotent shutdown.** An `Event` with a SIGINT handler ensures cleanup runs only once even if the user presses Ctrl+C multiple times.
* **Simplicity first.** This implementation focuses on the assignment goals (broadcasting to known peers, dynamic peers) and keeps out-of-scope features (encryption, persistent storage, complex gossip protocols). These can be added later.

---

## Message format (on the wire)

Each outgoing message is a JSON string. Example:

```json
{
  "type": "chat",
  "sender": "Heisenberg",
  "sender_id": "2f3c...-uuid",
  "text": "Hello everyone!",
  "timestamp": "2025-12-29T21:30:00.123456",
  "formatted": "[2025-12-29T21:30:00.123456] Heisenberg:
	Hello everyone!",
  "formatted_you": "[2025-12-29T21:30:00.123456] You:
	Hello everyone!"
}
```

**Receivers:**

* If `sender_id == my_sender_id` -> print `formatted_you`.
* Otherwise -> print `formatted`.

---

## How to run / usage

From the repo root (example uses `poetry` as in the project):

Start peers in separate terminals (or containers):

```bash
# Peer A (listens on 9001)
poetry run python -u -m snippets.lab3.exercise_tcp_group_chat 9001

# Peer B (listens on 9002, connects to A)
poetry run python -u -m snippets.lab3.exercise_tcp_group_chat 9002 127.0.0.1:9001

# Peer C (listens on 9003, connects to A and B)
poetry run python -u -m snippets.lab3.exercise_tcp_group_chat 9003 127.0.0.1:9001 127.0.0.1:9002
```

When started you will be prompted for a username:

```
Enter your username to start the chat:
```

**Commands available while running:**

* `/peers` - print known peer endpoints.
* `/quit` or `/exit` - graceful shutdown.
* Ctrl+C - graceful, idempotent shutdown.

**Notes:**

* `initial_peers` must be passed as `host:port` strings (the script uses the repo `address()` helper to parse them).
* If you start a peer with no initial peers and later another peer connects, the incoming connection will be registered and future broadcasts will reach it.
* The code prints informative messages for server listen events, incoming/outgoing connections, sends and errors.

---

## How to test (manual & quick scenarios)

**Basic 3-node test (as above):**

1. Start A on `9001`; enter username `Heisenberg`. You should see the server listening message.
2. Start B on `9002` connecting to `127.0.0.1:9001`; enter `Jesse`. B prints outgoing connection; A prints incoming connection.
3. Start C on `9003` connecting to `127.0.0.1:9001` and `127.0.0.1:9002`; enter `Salamanca`.
4. Type a message on Heisenberg: `Hello`. Expected:

   * Heisenberg sees `You:` line with timestamp.
   * Jesse and Salamanca see a line with `Heisenberg:` and the same timestamp and message.
5. On any peer run `/peers` to see known remote addresses.
6. Kill/close one peer with Ctrl+C: other peers show connection closed messages and continue working.

**Edge cases:**

* Send a message when there are no known peers: you get `[WARN] No peers connected, message not sent to anyone.`
* Start A, then B connects to A. Then B sends messages: A will receive and print them. If C later connects only to A, messages from B will not automatically be learned by C (see limitations below).
* Duplicate connections: if A connects to B and B connects to A, both connections exist; messages are sent on both - the `sender_id` prevents double-printing of locally-originated messages but the graph contains two edges. (Suggested improvement: deduplicate by endpoint.)

---

## How I tested locally (what I did)

* Launched three instances on different ports with the example arguments.
* Verified:

  * server listen messages,
  * outgoing connection logs,
  * that messages show as `You:` on the sender, and `Heisenberg:` / `Jesse:` / `Salamanca:` on remote peers,
  * `/peers` lists remote addresses,
  * graceful shutdown prints `Peer shutdown` and remote connections close on the other side.