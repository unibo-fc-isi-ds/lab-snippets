import sys
import queue
from node.node import Node
from ui.ui_tk import TkChatUI


def main():
	if len(sys.argv) < 3:
		print("Uso corretto:")
		print("   python exercise_tcp_group_chat.py <name> <port> [host:port ...]")
		print("Esempio:")
		print("   python exercise_tcp_group_chat.py Pippo 8000 127.0.0.1:8200 192.168.1.5:9001")
		return

	name = sys.argv[1]

	# controllo porta
	try:
		port = int(sys.argv[2])
	except ValueError:
		print(f"Errore: la porta deve essere un intero, ricevuto '{sys.argv[2]}'")
		return

	# parsing robusto peer iniziali
	peers = []
	for entry in sys.argv[3:]:
		if ":" not in entry:
			print(f"Errore nel peer '{entry}': formato corretto host:port")
			print("Esempio valido: 127.0.0.1:8200")
			return

		host, port_str = entry.split(":", 1)

		# validazione porta
		try:
			peer_port = int(port_str)
		except ValueError:
			print(f"Errore nel peer '{entry}': la porta deve essere un numero intero")
			return

		peers.append((host, peer_port))

	# queue per UI
	ui_queue = queue.Queue()

	# avvio nodo
	try:
		node = Node(name=name, port=port, peers=peers, queue_ui=ui_queue)
	except Exception as e:
		print("Errore durante l'avvio del nodo:", e)
		return

	# UI
	ui = TkChatUI(node)
	ui.start()


if __name__ == "__main__":
	main()
