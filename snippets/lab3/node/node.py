import socket
from core.message import Message
from core.status import Status
from connection.connection import Connection
from node.accept_thread import AcceptThread
from node.heartbeat_thread import HeartbeatThread
from uuid import uuid4


class Node:
	"""
	Nodo P2P TCP:
	- accept thread esterno
	- heartbeat thread esterno
	- gestione messaggi
	- rebroadcast
	"""

	def __init__(self, name, port, peers=None, queue_ui=None):
		self.status = Status(name, port)
		self.queue_ui = queue_ui

		# socket server TCP
		self.server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		self.server_socket.bind(("0.0.0.0", port))
		self.server_socket.listen()

		# avvio accept thread
		self.accept_thread = AcceptThread(self.server_socket, self, self.status)
		self.accept_thread.start()

		# avvio heartbeat thread
		self.heartbeat_thread = HeartbeatThread(self, self.status)
		self.heartbeat_thread.start()

		# connessioni outgoing
		if peers:
			for host, p in peers:
				self.connect_to_peer(host, p)

	def connect_to_peer(self, host, port):
		try:
			sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
			sock.connect((host, port))

			conn = Connection(sock, self, self.status)
			self.status.add_outgoing(conn)

			self.send_connect_message(conn)

		except Exception as e:
			print("Connessione fallita:", e)

	def send_connect_message(self, conn):
		msg = Message.new_connect(
			sender=self.status.node_name,
			name=self.status.node_name,
			port=self.status.port
		)
		conn.send(msg)

	def handle_message(self, msg, conn):
		# deduplica
		if self.status.has_seen(msg.msg_id):
			return
		self.status.mark_seen(msg.msg_id)

		# dispatch per tipo
		if msg.type == "connect":
			conn.peer_name = msg.payload.get("name")

		elif msg.type == "chat":
			if self.queue_ui:
				self.queue_ui.put(msg)

		elif msg.type == "heartbeat":
			self.status.update_heartbeat(conn)

		# rebroadcast verso gli altri peer
		self._rebroadcast(msg, conn)

	def _rebroadcast(self, msg, origin_conn):
		with self.status.lock:
			for c in (self.status.incoming + self.status.outgoing):
				if c is origin_conn:
					continue
				if c.alive:
					c.send(msg)

	def send_chat(self, text):
		msg = Message.new_chat(self.status.node_name, text)
		self.status.mark_seen(msg.msg_id)

		# MOSTRA SUBITO IL MESSAGGIO LOCALE
		if self.queue_ui:
			self.queue_ui.put(msg)

		self._rebroadcast(msg, None)

	def on_connection_closed(self, conn):
		"""
		Notifica locale della disconnessione del peer.
		"""
		name = conn.peer_name or "peer"

		# Messaggio solo per la UI locale
		system_msg = Message(
			msg_id="system-" + str(uuid4()),
			sender="SYSTEM",
			type_="info",
			payload=f"[{name}] disconnesso"
		)

		if self.queue_ui:
			self.queue_ui.put(system_msg)
