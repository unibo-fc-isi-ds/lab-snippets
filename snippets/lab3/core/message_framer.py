class MessageFramer:
	"""
	Incremental TCP message framer.

	TCP is a stream protocol: data may arrive fragmented or merged into
	arbitrary byte sequences. This component reconstructs *application-level*
	messages by splitting the incoming stream using a terminator (newline).

	Responsibilities:
	- accumulate arbitrary TCP byte chunks
	- detect and extract complete messages delimited by TERMINATOR
	- return zero or more complete raw message frames (bytes)
	- leave incomplete trailing bytes in the internal buffer
	"""

	# Application-level delimiter.
	# The Message class guarantees that each serialized message ends with "\n".
	TERMINATOR = b"\n"

	def __init__(self):
		# Internal FIFO buffer storing partial or full message fragments.
		self.buffer = b""

	def feed(self, data):
		"""
		Ingest a new TCP byte chunk and extract complete messages.

		Parameters:
			data (bytes): raw bytes received from socket.recv()

		Returns:
			list[bytes]: list of extracted full messages, WITHOUT the terminator.

		Notes:
			- TCP messages may arrive split across multiple recv() calls.
			- Multiple messages may arrive concatenated in a single recv().
			- This function must therefore support both scenarios.

		Algorithm:
			1. Append bytes to the internal buffer
			2. Search for TERMINATOR
			3. For each terminator found:
			   - slice the message (excluding the terminator)
			   - remove processed bytes from buffer
			4. Return all complete messages found (possibly 0, 1 or more)
		"""
		if not data:
			# No data, no messages
			return []

		# Extend internal buffer
		self.buffer += data
		messages = []

		while True:
			# Find next terminator in the aggregated buffer
			sep_index = self.buffer.find(self.TERMINATOR)
			if sep_index == -1:
				# No more complete messages available
				break

			# Extract a full message frame (slice excludes the terminator)
			raw_msg = self.buffer[:sep_index]
			messages.append(raw_msg)

			# Remove message + delimiter from the buffer
			self.buffer = self.buffer[sep_index + len(self.TERMINATOR):]

		return messages
