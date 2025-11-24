class MessageFramer:
	"""
	Gestisce l'accumulo dei dati TCP e lo split dei messaggi in base ad un
	terminatore arbitrario (default: b"\\0").
	"""

	TERMINATOR = b"\n"

	def __init__(self):
		self.buffer = b""

	def feed(self, data):
		"""
		Aggiunge nuovi byte al buffer interno e estrae
		tutti i messaggi completi delimitati dal terminatore.
		
		Ritorna:
			- list[bytes] : lista dei messaggi completi (senza terminatore)
		"""
		if not data:
			return []

		self.buffer += data
		messages = []

		while True:
			sep_index = self.buffer.find(self.TERMINATOR)
			if sep_index == -1:
				break

			raw_msg = self.buffer[:sep_index]
			messages.append(raw_msg)

			self.buffer = self.buffer[sep_index + len(self.TERMINATOR):]

		return messages
