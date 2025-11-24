import threading
import time


class Status:
	"""
	Shared state object accessed concurrently by multiple threads.

	It centralizes:
	- local node identity (name + port)
	- lists of active incoming and outgoing TCP connections
	- message-deduplication (set of seen msg_id)
	- peer-level deduplication for connect events
	- per-connection heartbeat timestamps
	- a global lock protecting all shared fields

	This object is intentionally minimal: it stores data and guarantees
	thread-safe access, while all higher-level logic stays in Node.
	"""

	def __init__(self, node_name, port):
		self.node_name = node_name
		self.port = port

		# Active TCP connections.
		self.incoming = []   # connections initiated by remote peers
		self.outgoing = []   # connections initiated by this node

		# Message-level deduplication: avoids rebroadcasting the same msg twice.
		self.seen_messages = set()

		# Peer-level deduplication: ensures one "peer connected" UI event per name.
		self.connected_peers = set()

		# Heartbeat timestamps: conn -> float (last heartbeat received)
		self.last_heartbeat = {}

		# Global lock protecting all shared state.
		self.lock = threading.Lock()

	# ----------------------------------------------------------------------
	# Connection registration
	# ----------------------------------------------------------------------

	def add_incoming(self, conn):
		"""
		Add an inbound connection and initialize its heartbeat timestamp.
		"""
		with self.lock:
			self.incoming.append(conn)
			self.last_heartbeat[conn] = time.time()

	def add_outgoing(self, conn):
		"""
		Add an outbound connection and initialize its heartbeat timestamp.
		"""
		with self.lock:
			self.outgoing.append(conn)
			self.last_heartbeat[conn] = time.time()

	def remove_connection(self, conn):
		"""
		Remove a connection from both inbound/outbound lists and
		delete its heartbeat entry. Called by Connection.close().
		"""
		with self.lock:
			if conn in self.incoming:
				self.incoming.remove(conn)
			if conn in self.outgoing:
				self.outgoing.remove(conn)
			if conn in self.last_heartbeat:
				del self.last_heartbeat[conn]

	# ----------------------------------------------------------------------
	# Message deduplication
	# ----------------------------------------------------------------------

	def has_seen(self, msg_id):
		"""
		Return True if msg_id was already processed.
		Thread-safe.
		"""
		with self.lock:
			return msg_id in self.seen_messages

	def mark_seen(self, msg_id):
		"""
		Record a message identifier as processed.
		Thread-safe.
		"""
		with self.lock:
			self.seen_messages.add(msg_id)

	# ----------------------------------------------------------------------
	# Heartbeat tracking
	# ----------------------------------------------------------------------

	def update_heartbeat(self, conn):
		"""
		Update last heartbeat timestamp for the given connection.
		Called whenever a heartbeat message is received.
		"""
		with self.lock:
			self.last_heartbeat[conn] = time.time()

	def get_stale_connections(self, timeout):
		"""
		Return a list of connections whose heartbeat exceeds the given timeout.
		No side effects: removal is handled by the caller (HeartbeatThread).
		"""
		now = time.time()
		stale = []

		with self.lock:
			for conn, ts in list(self.last_heartbeat.items()):
				if now - ts > timeout:
					stale.append(conn)

		return stale
