import socket
from uuid import uuid4
from core.message import Message
from core.status import Status
from connection.connection import Connection
from node.accept_thread import AcceptThread
from node.heartbeat_thread import HeartbeatThread


class Node:
	"""
	Core P2P node.
	Each instance:
	- listens for incoming TCP connections
	- establishes outgoing TCP connections (optional)
	- maintains connection state and deduplication
	- handles messages (connect/chat/heartbeat)
	- rebroadcasts messages across its local view of the network
	"""

	def __init__(self, name, port, peers=None, queue_ui=None):
		# shared global state (connections, dedup, heartbeats)
		self.status = Status(name, port)

		# optional UI queue for asynchronous delivery of display messages
		self.queue_ui = queue_ui

		# configure TCP listening socket
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_socket.bind(("0.0.0.0", port))
		self.server_socket.listen()

		# async acceptor thread for inbound connections
		self.accept_thread = AcceptThread(self.server_socket, self, self.status)
		self.accept_thread.start()

		# async heartbeat thread (keeps connections monitored and closes stale peers)
		self.heartbeat_thread = HeartbeatThread(self, self.status)
		self.heartbeat_thread.start()

		# optional outgoing connections given at launch time
		if peers:
			for host, p in peers:
				self.connect_to_peer(host, p)

	# ----------------------------------------------------------------------
	# OUTGOING CONNECTION ESTABLISHMENT
	# ----------------------------------------------------------------------
	def connect_to_peer(self, host, port):
		"""
		Attempt to connect to another peer. If successful:
		- wrap the socket in a Connection object
		- register it as outgoing
		- send an initial connect message

		The connection attempt is synchronous by design.
		"""

		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((host, port))

			conn = Connection(sock, self, self.status)
			self.status.add_outgoing(conn)

			# notify remote peer of local identity
			self.send_connect_message(conn)

			# notify local UI
			if self.queue_ui:
				system_msg = Message(
					msg_id="system-" + str(uuid4()),
					sender="SYSTEM",
					type_="info",
					payload=f"Connected to peer {host}:{port}"
				)
				self.queue_ui.put(system_msg)

		except Exception as e:
			# minimal error reporting
			print("Connessione fallita:", e)

	# ----------------------------------------------------------------------
	# SEND INITIAL CONNECT MESSAGE
	# ----------------------------------------------------------------------
	def send_connect_message(self, conn):
		"""
		Send a connect-type message to the remote peer,
		informing it of the local node's name and port.
		"""

		msg = Message.new_connect(
			sender=self.status.node_name,
			name=self.status.node_name,
			port=self.status.port
		)
		conn.send(msg)

	# ----------------------------------------------------------------------
	# MAIN MESSAGE DISPATCHER
	# ----------------------------------------------------------------------
	def handle_message(self, msg, conn):
		"""
		Main entry for all incoming messages from ReaderThread.

		Responsibilities:
		- deduplication (ignore known msg_id)
		- dispatch by message type
		- rebroadcast to all connected peers except the sender
		"""

		# deduplication check
		if self.status.has_seen(msg.msg_id):
			return
		self.status.mark_seen(msg.msg_id)

		# --------------------
		# CONNECT MESSAGE
		# --------------------
		if msg.type == "connect":
			conn.peer_name = msg.payload.get("name")
			peer = conn.peer_name

			# deduplicate per-peer connection notifications
			with self.status.lock:
				first_time = peer not in self.status.connected_peers
				self.status.connected_peers.add(peer)

			# notify UI only the first time this peer appears
			if first_time and self.queue_ui:
				system_msg = Message(
					msg_id="system-" + str(uuid4()),
					sender="SYSTEM",
					type_="info",
					payload=f"[{peer}] connected"
				)
				self.queue_ui.put(system_msg)

		# --------------------
		# CHAT MESSAGE
		# --------------------
		elif msg.type == "chat":
			# pass-through to UI (local display)
			if self.queue_ui:
				self.queue_ui.put(msg)

		# --------------------
		# HEARTBEAT MESSAGE
		# --------------------
		elif msg.type == "heartbeat":
			# update timestamp for connection liveness checks
			self.status.update_heartbeat(conn)

		# broadcast to all other peers (fan-out)
		self._rebroadcast(msg, conn)

	# ----------------------------------------------------------------------
	# MESSAGE REBROADCAST
	# ----------------------------------------------------------------------
	def _rebroadcast(self, msg, origin_conn):
		"""
		Send the message to all active connections except the origin.
		This creates a flooding broadcast across the current local graph.
		"""

		with self.status.lock:
			for c in (self.status.incoming + self.status.outgoing):
				if c is origin_conn:
					continue
				if c.alive:
					c.send(msg)

	# ----------------------------------------------------------------------
	# LOCAL SEND CHAT
	# ----------------------------------------------------------------------
	def send_chat(self, text):
		"""
		Create a chat message and broadcast it immediately.
		Local display is inserted before rebroadcast.

		Deduplication marks the message as seen to avoid looping back.
		"""

		msg = Message.new_chat(self.status.node_name, text)
		self.status.mark_seen(msg.msg_id)

		if self.queue_ui:
			self.queue_ui.put(msg)

		self._rebroadcast(msg, None)

	# ----------------------------------------------------------------------
	# CONNECTION CLOSED CALLBACK
	# ----------------------------------------------------------------------
	def on_connection_closed(self, conn):
		"""
		Called by Connection.close() when a socket dies.
		Used only for local UI notifications.
		"""

		name = conn.peer_name or "peer"

		system_msg = Message(
			msg_id="system-" + str(uuid4()),
			sender="SYSTEM",
			type_="info",
			payload=f"[{name}] disconnesso"
		)

		if self.queue_ui:
			self.queue_ui.put(system_msg)
