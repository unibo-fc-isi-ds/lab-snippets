import threading
from connection.connection import Connection


class AcceptThread(threading.Thread):
	"""
	Background thread responsible for accepting new inbound TCP connections.

	This isolates blocking accept() from the main Node logic and allows:
	- concurrent handling of multiple connections
	- clean shutdown (the thread stops when the server socket is closed)
	- creation of a dedicated Connection instance per incoming socket

	The thread is daemonized so it will not prevent process termination.
	"""

	def __init__(self, server_socket, node, status):
		"""
		server_socket: the listening TCP socket owned by the Node
		node: Node instance, used so the created Connection can call back
		status: shared Status object tracking incoming/outgoing connections
		"""
		super().__init__(daemon=True)
		self.server_socket = server_socket
		self.node = node
		self.status = status

	def run(self):
		"""
		Main loop:
		- blocks on accept()
		- wraps each socket with a Connection object
		- registers the connection in the shared Status

		The loop ends automatically when the server socket is closed.
		"""

		while True:
			try:
				sock, addr = self.server_socket.accept()
			except OSError:
				# If the listening socket is closed, accept() fails and the thread terminates.
				break

			# create a Connection object with its own reader thread
			conn = Connection(sock, self.node, self.status)

			# register the inbound connection
			self.status.add_incoming(conn)
