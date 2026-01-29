import threading
from core.message import Message


class HeartbeatThread(threading.Thread):
	"""
	Periodic background thread responsible for connection liveness.
	Responsibilities:
	- periodically send heartbeat messages to all known peers
	- detect stale connections (missing heartbeats)
	- close dead connections so the system can cleanly recover

	The thread is daemonized because it should not block process exit.
	"""

	def __init__(self, node, status, interval=5, timeout=15):
		"""
		node: Node instance, used only for callbacks if needed
		status: shared Status instance (connections, timestamps, locks)
		interval: how often to send a heartbeat (seconds)
		timeout: heartbeat expiration threshold (seconds)
		"""

		super().__init__(daemon=True)
		self.node = node
		self.status = status
		self.interval = interval
		self.timeout = timeout

	def run(self):
		"""
		Main loop:
		- sleep without busy-waiting
		- build heartbeat message
		- broadcast it to every active connection
		- compute stale peers and close them

		No exit condition is required for this project; the thread
		lives as long as the application runs.
		"""

		while True:
			# sleep interval without blocking the GIL
			threading.Event().wait(self.interval)

			# build heartbeat message; mark as seen to avoid rebroadcast loops
			msg = Message.new_heartbeat(self.status.node_name)
			self.status.mark_seen(msg.msg_id)

			# send heartbeat to all connections
			with self.status.lock:
				peers = self.status.incoming + self.status.outgoing
				for conn in peers:
					if conn.alive:
						conn.send(msg)

			# detect stale connections (no heartbeat received for too long)
			stale_list = self.status.get_stale_connections(self.timeout)

			# close unreachable peers; the connection layer
			# will trigger Node.on_connection_closed()
			for conn in stale_list:
				conn.close()
