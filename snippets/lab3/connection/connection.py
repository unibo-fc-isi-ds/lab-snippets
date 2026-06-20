import socket
from core.message_framer import MessageFramer
from connection.reader_thread import ReaderThread
from core.message import Message


class Connection:
	"""
	Represents a single TCP connection to a remote peer.

	This class encapsulates:
	- the underlying TCP socket
	- the framing logic (MessageFramer) used to reconstruct messages
	  from the TCP byte-stream
	- a dedicated ReaderThread responsible for receiving data and
	  dispatching complete messages to the Node
	- the lifetime of the connection (alive flag, cleanup on close)

	Notes:
	- Each Connection owns exactly one ReaderThread.
	- All outgoing messages are sent via the send() method, which expects
	  already-validated Message objects.
	"""

	def __init__(self, sock, node, status):
		"""
		Parameters:
			sock  (socket.socket): connected TCP socket
			node  (Node): reference to the owning node
			status(Status): shared state object for incoming/outgoing lists

		Sets up the connection, initializes the TCP framer and starts the
		reader thread responsible for handling incoming data.
		"""
		self.sock = sock
		self.node = node
		self.status = status
		self.peer_name = None  # becomes known after receiving a CONNECT message

		# Each connection has its own incremental TCP framer.
		self.framer = MessageFramer()
		self.alive = True

		# Launch the per-connection reader thread.
		self.reader = ReaderThread(self)
		self.reader.start()

	def send(self, msg):
		"""
		Send a Message object over the TCP connection.

		Behavior:
			- serializes the Message to JSON + terminator
			- writes it with sendall(), ensuring full delivery
			- in case of any socket error, the connection is closed

		Parameters:
			msg (Message): the message object to send
		"""
		if not isinstance(msg, Message):
			raise TypeError("Connection.send() requires a Message instance")

		try:
			raw = msg.to_json_bytes()
			self.sock.sendall(raw)
		except Exception:
			# Any exception during send means the connection is no longer valid.
			self.close()

	def close(self):
		"""
		Idempotent connection shutdown.

		Steps performed:
			1. Prevent repeated closure using `alive` flag.
			2. Close the underlying socket.
			3. Remove this Connection instance from Status (incoming/outgoing).
			4. Notify the Node so it can update UI and internal tracking.

		This method is always called by ReaderThread on exit, guaranteeing
		cleanup regardless of the shutdown mode (EOF, reset, exception).
		"""
		if not self.alive:
			return

		self.alive = False

		try:
			self.sock.close()
		except:
			pass  # socket already dead or invalid

		# Remove from status and notify node logic.
		self.status.remove_connection(self)
		self.node.on_connection_closed(self)
