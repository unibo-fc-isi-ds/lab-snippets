import threading
import traceback
from core.message import Message


class ReaderThread(threading.Thread):
	"""
	Per-connection TCP reader thread.

	Responsibilities:
	- continuously read raw bytes from a TCP socket
	- handle TCP stream fragmentation/aggregation through the MessageFramer
	- parse complete JSON messages into Message objects
	- forward valid messages to the owning Node instance
	- detect clean/unclean peer disconnects and trigger connection cleanup

	Notes:
	- This thread is intentionally dedicated to a *single* TCP connection.
	- recv() is blocking by design; thread stays dormant when no data arrives.
	"""

	def __init__(self, conn):
		"""
		Parameters:
			conn (Connection): the owning Connection wrapper, providing
			                   socket, node reference, and framing logic.
		"""
		super().__init__(daemon=True)

		self.conn = conn
		self.sock = conn.sock
		self.node = conn.node
		self.framer = conn.framer  # shared incremental TCP framer

	def run(self):
		"""
		Main receive loop.

		The logic is:
			1. recv() bytes from socket
			2. feed bytes to MessageFramer
			3. for each complete frame → parse as JSON → dispatch to Node
			4. break when socket closes or peer resets connection
		"""
		try:
			while self.conn.alive:

				try:
					# Blocking read — may return partial, full, multiple messages.
					data = self.sock.recv(4096)

				except ConnectionResetError:
					# The remote peer terminated the TCP connection abruptly.
					# This is normal under Windows or when processes exit.
					break

				# Empty byte-string → remote peer performed a clean shutdown.
				if not data:
					break

				# Reconstruct one or more message frames.
				messages = self.framer.feed(data)

				for raw in messages:
					# Parse application-level JSON message.
					msg = Message.from_raw_json(raw)

					if msg is None:
						# Malformed or incomplete JSON → safely ignore.
						continue

					# Forward valid messages to Node for higher-level logic.
					self.node.handle_message(msg, self.conn)

		except Exception:
			# Unexpected runtime error (not normal disconnects).
			# Print traceback for debugging and move on.
			traceback.print_exc()

		finally:
			# Always ensure connection cleanup.
			# This removes the connection from Status and triggers UI events.
			self.conn.close()
