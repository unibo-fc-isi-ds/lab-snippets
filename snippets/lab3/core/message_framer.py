class MessageFramer:
	"""
	Gestisce l'accumulo dei dati TCP e lo split dei messaggi in base ad un
	terminatore arbitrario (default: b"\\0").
	"""

	TERMINATOR = b"\0"

	def __init__(self):
		self.buffer = b""

	def feed(self, data):
		"""
		Aggiunge nuovi byte al buffer interno e estrae
		tutti i messaggi completi delimitati dal terminatore.
		
		Ritorna:
			- list[bytes] : lista dei messaggi completi (senza terminatore)
		"""
		self.buffer += data
		messages = []

		while True:
			# cerca il terminatore
			sep_index = self.buffer.find(self.TERMINATOR)

			# nessun messaggio completo
			if sep_index == -1:
				break

			# estrai bytes del messaggio
			raw_msg = self.buffer[:sep_index]
			messages.append(raw_msg)

			# rimuovi messaggio + terminatore dal buffer
			self.buffer = self.buffer[sep_index + len(self.TERMINATOR):]

		return messages
