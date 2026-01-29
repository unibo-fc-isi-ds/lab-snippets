import tkinter as tk
from tkinter import scrolledtext
import threading


class TkChatUI:
	def __init__(self, node):
		self.node = node
		self.msg_queue = node.queue_ui
		self.stop = False

		# main window
		self.root = tk.Tk()
		self.root.title(f"TCP Chat – {node.status.node_name}")

		# message area (read-only)
		self.msg_area = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, height=20, state=tk.DISABLED)
		self.msg_area.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)

		# input area
		self.input_area = tk.Entry(self.root)
		self.input_area.pack(fill=tk.X, padx=5, pady=5)
		self.input_area.bind("<Return>", self._on_enter)

		# periodic queue polling
		self.root.after(100, self._poll_queue)

	def _on_enter(self, event=None):
		text = self.input_area.get().strip()
		if not text:
			return

		if text.lower() == "exit":
			self.stop = True
			self.root.destroy()
			return

		self.node.send_chat(text)
		self.input_area.delete(0, tk.END)

	def _poll_queue(self):
		"""
		Periodically called by Tkinter's mainloop.
		Reads and displays messages from the queue.
		"""
		if self.stop:
			return

		while not self.msg_queue.empty():
			# message from the node
			msg = self.msg_queue.get()

			self.msg_area.config(state=tk.NORMAL)
			self.msg_area.insert(tk.END, f"[{msg.sender}] {msg.payload}\n")
			self.msg_area.config(state=tk.DISABLED)
			self.msg_area.see(tk.END)

		self.root.after(100, self._poll_queue)  # schedule next poll

	def start(self):
		self.root.mainloop()
		self.stop = True
