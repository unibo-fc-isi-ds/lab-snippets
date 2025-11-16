import threading
from connection import Connection


class AcceptThread(threading.Thread):
	"""
	Thread che accetta nuove connessioni TCP
	e le registra nello Status.
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
				break

			conn = Connection(sock, self.node, self.status)
			self.status.add_incoming(conn)
