import socket
from core.message_framer import MessageFramer
from connection.reader_thread import ReaderThread
from core.message import Message


class Connection:
	"""
	Gestisce una singola connessione TCP verso un peer.
	Avvia un ReaderThread che riceve dati, esegue framing
	e consegna i messaggi al nodo.
	"""

	def __init__(self, sock, node, status):
		self.sock = sock
		self.node = node
		self.status = status
		self.peer_name = None

		self.framer = MessageFramer()
		self.alive = True

		# avvia thread di lettura
		self.reader = ReaderThread(self)
		self.reader.start()

	def send(self, msg):
		"""
		Invia un oggetto Message serializzato.
		In caso di errore chiude la connessione.
		"""
		if not isinstance(msg, Message):
			raise TypeError("Connection.send() richiede un oggetto Message")

		try:
			raw = msg.to_json_bytes()
			self.sock.sendall(raw)
		except Exception:
			self.close()

	def close(self):
		"""
		Chiusura idempotente della connessione.
		Rimuove la connessione dallo stato e notifica il nodo.
		"""
		if not self.alive:
			return

		self.alive = False

		try:
			self.sock.close()
		except:
			pass

		self.status.remove_connection(self)
		self.node.on_connection_closed(self)
