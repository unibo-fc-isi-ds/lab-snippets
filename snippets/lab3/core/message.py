import json
from uuid import uuid4


class Message:
	"""
	Rappresenta un messaggio interno al sistema.
	Permette:
	- creazione facile (chat, connect, heartbeat)
	- validazione campi
	- conversione JSON ↔ oggetto Message
	"""

	TERMINATOR = "\n"

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
		"""
		Serializza il messaggio in JSON e aggiunge il terminatore,
		pronto per il socket.send().
		"""
		obj = {
			"msg_id": self.msg_id,
			"sender": self.sender,
			"type": self.type,
			"payload": self.payload
		}

		raw = json.dumps(obj) + self.TERMINATOR
		return raw.encode("utf-8")

	# ----------------------------
	# DESERIALIZZAZIONE
	# ----------------------------

	@classmethod
	def from_raw_json(cls, raw_bytes):
		"""
		Converte un JSON in bytes in un oggetto Message.
		Restituisce None se JSON invalido o mancante di campi obbligatori.
		"""
		try:
			obj = json.loads(raw_bytes.decode("utf-8"))
		except:
			return None

		# validazione minima
		if ("msg_id" not in obj or
			"sender" not in obj or
			"type" not in obj or
			"payload" not in obj):
			return None

		return cls(
			msg_id=obj["msg_id"],
			sender=obj["sender"],
			type_=obj["type"],
			payload=obj["payload"]
		)
