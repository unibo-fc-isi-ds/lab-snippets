import socket
from connection.reader_thread import ReaderThread


class Connection:
	"""
	Rappresenta una singola connessione TCP verso un altro nodo.
	Ha un reader thread esterno che gestisce la lettura.
	"""

	def __init__(self, sock, node, status):
		self.sock = sock
		self.node = node
		self.status = status
		self.peer_name = None
		self.framer = MessageFramer()
		self.alive = True

		# avvio reader thread
		self.reader = ReaderThread(self)
		self.reader.start()

	def send(self, msg):
		try:
			raw = msg.to_json_bytes()
			self.sock.sendall(raw)
		except Exception:
			self.close()

	def close(self):
		if not self.alive:
			return
		self.alive = False

		try:
			self.sock.close()
		except:
			pass

		self.status.remove_connection(self)
		self.node.on_connection_closed(self)
