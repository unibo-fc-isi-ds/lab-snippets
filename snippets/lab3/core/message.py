import json
from uuid import uuid4


class Message:
	"""
	Internal message representation used by the TCP P2P chat.

	This class defines:
	- factories for the supported message types (chat, connect, heartbeat)
	- conversion from Message → JSON bytes (framed using a terminator)
	- conversion from raw JSON bytes → Message object

	The design separates message semantics from transport concerns:
	the Connection and ReaderThread handle socket I/O,
	while this class only defines the message format.
	"""

	# Line-based framing: each message ends with a newline.
	# The MessageFramer uses the same terminator.
	TERMINATOR = b"\n"

	def __init__(self, msg_id, sender, type_, payload):
		"""
		Parameters:
			msg_id  : unique identifier for deduplication
			sender  : logical name of node originating the message
			type_   : message category (chat/connect/heartbeat/info/custom)
			payload : message body (string or dict depending on type)
		"""
		self.msg_id = msg_id
		self.sender = sender
		self.type = type_
		self.payload = payload

	# ----------------------------------------------------------------------
	# Factory methods
	# ----------------------------------------------------------------------

	@classmethod
	def new_chat(cls, sender, text):
		"""
		Create a chat message whose payload is the text body.
		"""
		return cls(
			msg_id=str(uuid4()),
			sender=sender,
			type_="chat",
			payload=text
		)

	@classmethod
	def new_connect(cls, sender, name, port):
		"""
		Create a connection announcement.
		Sent once when a new TCP connection is established.
		"""
		return cls(
			msg_id=str(uuid4()),
			sender=sender,
			type_="connect",
			payload={"name": name, "port": port}
		)

	@classmethod
	def new_heartbeat(cls, sender):
		"""
		Create a heartbeat message (empty payload).
		Used for liveness detection and timeout-based disconnection.
		"""
		return cls(
			msg_id=str(uuid4()),
			sender=sender,
			type_="heartbeat",
			payload={}
		)

	# ----------------------------------------------------------------------
	# Serialization
	# ----------------------------------------------------------------------

	def to_json_bytes(self):
		"""
		Serialize the message as a JSON object with a newline terminator.

		This method does NOT apply any framing logic besides appending
		the terminator — framing is handled entirely by MessageFramer.
		"""
		obj = {
			"msg_id": self.msg_id,
			"sender": self.sender,
			"type": self.type,
			"payload": self.payload
		}

		# Always produce UTF-8 encoded bytes + terminator
		return json.dumps(obj).encode("utf-8") + self.TERMINATOR

	# ----------------------------------------------------------------------
	# Deserialization
	# ----------------------------------------------------------------------

	@classmethod
	def from_raw_json(cls, raw_bytes):
		"""
		Reconstruct a Message from raw JSON bytes.

		Returns:
			Message instance or None if the JSON is malformed or missing fields.

		We keep this method strict on purpose: malformed messages are discarded
		and never injected into the logic.
		"""
		try:
			text = raw_bytes.decode("utf-8").strip()
			obj = json.loads(text)
		except Exception:
			# Invalid UTF-8 or invalid JSON structure
			return None

		required = ("msg_id", "sender", "type", "payload")
		if not all(f in obj for f in required):
			# Missing required fields → ignore silently
			return None

		return cls(
			msg_id=obj["msg_id"],
			sender=obj["sender"],
			type_=obj["type"],
			payload=obj["payload"]
		)
