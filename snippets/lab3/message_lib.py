import uuid
import json

def make_message(text, sender):
	return json.dumps({
		"id": str(uuid.uuid4()),
		"sender": sender,
		"text": text
	})

def parse_message(payload):
	try:
		return json.loads(payload)
	except json.JSONDecodeError:
		return None
