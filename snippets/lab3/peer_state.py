from snippets.lab3 import *
from message_lib import make_message, parse_message
import json
import threading

class PeerState:
	def __init__(self, username, listen_port, initial_peers):
		# configurazione
		self.username = username
		self.listen_port = listen_port
		self.initial_peers = initial_peers		# lista di "host:port"

		# stato runtime
		self.peers = set()						# connessioni attive
		self.already_seen = set()				# msg_id già visti
		self.lock = threading.Lock()

		# server locale (settato nel main)
		self.server = None

	# =======================================================
	# REGISTRAZIONE PEER
	# =======================================================

	def add_peer(self, connection):
		with self.lock:
			self.peers.add(connection)

	def remove_peer(self, connection):
		with self.lock:
			if connection in self.peers:
				self.peers.remove(connection)

	# =======================================================
	# MESSAGE HANDLING (anti-loop)
	# =======================================================

	def has_seen(self, msg_id):
		with self.lock:
			return msg_id in self.already_seen

	def remember(self, msg_id):
		with self.lock:
			self.already_seen.add(msg_id)

	# =======================================================
	# BROADCAST
	# =======================================================

	def broadcast(self, msg_json, exclude=None):
		with self.lock:
			for p in list(self.peers):
				if p is exclude:
					continue
				try:
					p.send(msg_json)
                # se fallisce elimino il peer
				except:
					self.peers.discard(p)

	# =======================================================
	# CALLBACK: NUOVO MESSAGGIO
	# =======================================================

	def on_message_received(self, event, payload, connection, error):
		match event:
			case 'message':
				msg = parse_message(payload)
				if msg is None:
					return

				msg_id = msg.get("id")
				if self.has_seen(msg_id):
					return

				self.remember(msg_id)

				sender = msg.get("sender", "unknown")
				text = msg.get("text", "")
				print(f"{sender}: {text}")

				# rebroadcast agli altri
				self.broadcast(payload, exclude=connection)

			case 'close':
				print(f"Connessione chiusa con {connection.remote_address}")
				self.remove_peer(connection)

			case 'error':
				print(error)
				self.remove_peer(connection)

	# =======================================================
	# CALLBACK: NUOVA CONNESSIONE
	# =======================================================

	def on_new_connection(self, event, connection, address, error):
		match event:
			case 'listen':
				print(f"Peer ascolta su {address[0]} (IP: {', '.join(local_ips())})")

			case 'connect':
				print(f"Connessione entrante da {address}")
				connection.callback = self.on_message_received
				self.add_peer(connection)

			case 'stop':
				print("Stop ascolto nuove connessioni")

			case 'error':
				print(error)

	# =======================================================
	# CONNESSONE PEER DA CLI
	# =======================================================

	def connect_to_initial_peers(self):
		for entry in self.initial_peers:
			host, port = entry.split(":")
			try:
				c = Client((host, int(port)), self.on_message_received)
				print(f"Connesso a {c.remote_address}")
				self.add_peer(c)
			except Exception as e:
				print(f"Connessione a {entry} fallita: {e}")
