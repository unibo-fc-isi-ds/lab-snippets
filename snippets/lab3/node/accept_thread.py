import threading
from connection.connection import Connection


class AcceptThread(threading.Thread):
	"""
	Thread che accetta nuove connessioni TCP
	e crea oggetti Connection corrispondenti.
	"""

	def __init__(self, server_socket, node, status):
		super().__init__(daemon=True)
		self.server_socket = server_socket
		self.node = node
		self.status = status

	def run(self):
		while True:
			try:
				sock, addr = self.server_socket.accept()
			except OSError:
				# server socket chiuso → termina thread
				break

			conn = Connection(sock, self.node, self.status)
			self.status.add_incoming(conn)
