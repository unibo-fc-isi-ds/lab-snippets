import threading
import traceback
from core.message import Message


class ReaderThread(threading.Thread):
	def __init__(self, conn):
		super().__init__(daemon=True)
		self.conn = conn
		self.sock = conn.sock
		self.node = conn.node
		self.framer = conn.framer

	def run(self):
		try:
			while self.conn.alive:
				try:
					data = self.sock.recv(4096)
				except ConnectionResetError:
					# normale: peer chiuso bruscamente
					break


				if not data:
					break

				messages = self.framer.feed(data)

				for raw in messages:

					msg = Message.from_raw_json(raw)

					if msg is None:
						continue

					self.node.handle_message(msg, self.conn)

		except Exception as e:
			# errori reali, NON disconnessioni normali
			traceback.print_exc()

		finally:
			self.conn.close()
