import threading
from core.message import Message


class HeartbeatThread(threading.Thread):
	"""
	Thread periodico:
	- invia heartbeat ogni 5 secondi
	- controlla connessioni stale
	"""

	def __init__(self, node, status, interval=5, timeout=15):
		super().__init__(daemon=True)
		self.node = node
		self.status = status
		self.interval = interval
		self.timeout = timeout

	def run(self):
		while True:
			# attesa non-busy
			threading.Event().wait(self.interval)

			# crea heartbeat
			msg = Message.new_heartbeat(self.status.node_name)
			self.status.mark_seen(msg.msg_id)

			# invio a tutti i peer
			with self.status.lock:
				peers = self.status.incoming + self.status.outgoing
				for conn in peers:
					if conn.alive:
						conn.send(msg)

			# rileva connessioni stale
			stale_list = self.status.get_stale_connections(self.timeout)
			for conn in stale_list:
				conn.close()
