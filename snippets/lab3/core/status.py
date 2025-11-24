import threading
import time


class Status:
	"""
	Stato condiviso tra tutti i thread.
	Contiene:
	- nome nodo locale
	- porta locale
	- connessioni entranti
	- connessioni uscenti
	- set di msg_id già visti (deduplica)
	- lock globale
	- timestamp heartbeat per ogni connessione
	"""

	def __init__(self, node_name, port):
		self.node_name = node_name
		self.port = port

		self.incoming = []
		self.outgoing = []

		self.seen_messages = set()

		self.last_heartbeat = {}	# conn → timestamp

		self.lock = threading.Lock()

	# -------------------------------
	# Gestione connessioni
	# -------------------------------

	def add_incoming(self, conn):
		with self.lock:
			self.incoming.append(conn)
			self.last_heartbeat[conn] = time.time()

	def add_outgoing(self, conn):
		with self.lock:
			self.outgoing.append(conn)
			self.last_heartbeat[conn] = time.time()

	def remove_connection(self, conn):
		# rimozione connessione + relativa entry heartbeat
		with self.lock:
			if conn in self.incoming:
				self.incoming.remove(conn)
			if conn in self.outgoing:
				self.outgoing.remove(conn)
			if conn in self.last_heartbeat:
				del self.last_heartbeat[conn]

	# -------------------------------
	# Deduplica
	# -------------------------------

	def has_seen(self, msg_id):
		with self.lock:
			return msg_id in self.seen_messages

	def mark_seen(self, msg_id):
		with self.lock:
			self.seen_messages.add(msg_id)

	# -------------------------------
	# Heartbeat tracking
	# -------------------------------

	def update_heartbeat(self, conn):
		with self.lock:
			self.last_heartbeat[conn] = time.time()

	def get_stale_connections(self, timeout):
		now = time.time()
		stale = []

		with self.lock:
			for conn, ts in list(self.last_heartbeat.items()):
				if now - ts > timeout:
					stale.append(conn)

		return stale
