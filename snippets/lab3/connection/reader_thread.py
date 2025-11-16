import threading
import traceback
from framer import MessageFramer
from snippets.lab3.core.message import Message


class ReaderThread(threading.Thread):
	"""
	Thread di lettura associato ad una Connection.
	Legge dal socket, esegue framing, crea Message
	e invoca node.handle_message(msg, conn).
	"""

	def __init__(self, conn):
		super().__init__(daemon=True)
		self.conn = conn
		self.sock = conn.sock
		self.node = conn.node
		self.status = conn.status
		self.framer = conn.framer

	def run(self):
		try:
			while self.conn.alive:
				data = self.sock.recv(4096)
				if not data:
					break

				messages = self.framer.feed(data)

				for raw in messages:
					msg = Message.from_raw_json(raw)
					if msg is None:
						continue

					self.node.handle_message(msg, self.conn)

		except Exception:
			traceback.print_exc()

		finally:
			self.conn.close()
