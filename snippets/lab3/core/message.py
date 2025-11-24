import json
from uuid import uuid4


class Message:
	"""
	Rappresenta un messaggio interno al sistema.
	- factory per chat, connect, heartbeat
	- serializzazione JSON → bytes
	- deserializzazione bytes → Message
	"""

	TERMINATOR = b"\n"

	def __init__(self, msg_id, sender, type_, payload):
		self.msg_id = msg_id
		self.sender = sender
		self.type = type_
		self.payload = payload

	# ----------------------------
	# FACTORY METHODS
	# ----------------------------

	@classmethod
	def new_chat(cls, sender, text):
		return cls(
			msg_id=str(uuid4()),
			sender=sender,
			type_="chat",
			payload=text
		)

	@classmethod
	def new_connect(cls, sender, name, port):
		return cls(
			msg_id=str(uuid4()),
			sender=sender,
			type_="connect",
			payload={"name": name, "port": port}
		)

	@classmethod
	def new_heartbeat(cls, sender):
		return cls(
			msg_id=str(uuid4()),
			sender=sender,
			type_="heartbeat",
			payload={}
		)

	# ----------------------------
	# SERIALIZZAZIONE
	# ----------------------------

	def to_json_bytes(self):
		obj = {
			"msg_id": self.msg_id,
			"sender": self.sender,
			"type": self.type,
			"payload": self.payload
		}

		return json.dumps(obj).encode("utf-8") + self.TERMINATOR

	# ----------------------------
	# DESERIALIZZAZIONE
	# ----------------------------

	@classmethod
	def from_raw_json(cls, raw_bytes):
		try:
			text = raw_bytes.decode("utf-8").strip()
			obj = json.loads(text)
		except:
			return None

		required = ("msg_id", "sender", "type", "payload")
		if not all(f in obj for f in required):
			return None

		return cls(
			msg_id=obj["msg_id"],
			sender=obj["sender"],
			type_=obj["type"],
			payload=obj["payload"]
		)
