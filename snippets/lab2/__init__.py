from datetime import datetime
import psutil
import socket

# questo metodo prende ip e la porta passata, verifica che siano valori validi
# e poi restituisce una tupla che contiene Indirizzo IP e numero della porta
def address(ip='0.0.0.0:0', port=None):
    ip = ip.strip() # rimuove da stringa ip tutti gli spazi bianchi
    if ':' in ip: #se trova dentro ip il carattere ":", divide in 2 per separare port da indirizzo ip
        ip, p = ip.split(':')
        p = int(p)
        port = port or p # qui metto la port p trovata dentro la stringa iniziale se c'era
    if port is None: # se non trova niente di niente, allora mette come port 0
        port = 0
    assert port in range(0, 65536), "Port number must be in the range 0-65535" 
    assert isinstance(ip, str), "IP address must be a string"
    return ip, port


# questo metodo restituisce una nuova stringa che contiene al suo interno il momento in cui è stato inviato un messaggio,
# chi lo ha inviato, e il testo del messaggio
def message(text: str, sender: str, timestamp: datetime=None):
    if timestamp is None:
        timestamp = datetime.now()
    return f"[{timestamp.isoformat()}] {sender}:\n\t{text}"

# tramite questo metodo recuperiamo tutti i possibili indirizzi IP disponibili della macchina locale
# ci servono tutti gli indirizzi IP per poter comunicare con le altre persone
def local_ips():
    for interface in psutil.net_if_addrs().values():
        for addr in interface:
            if addr.family == socket.AF_INET:
                    yield addr.address


# la classe che indica uno dei tanti peers che sono presenti in un sistema UDP (ogni Peer è un utente)
# un Peer è un oggetto che permette di inviare e ricevere messaggi su Network tramite UDP socket
# usiamo Peer per fare sì che ogni macchina possa interagire con molteplici utenti! (dobbiamo tenere traccia di altri partecipanti)
# incapsula al suo interno un socket e una lista di tutti i peers partecipanti
class Peer:
    # ogni Peer prende in ingresso un numero di porta e una set di tutti gli altri peers (tuple indirizzo ip e porta)
    # il numero della port ci serve poichè il nostro peer dovrà ascoltare messaggi in arrivo, quando si ascolta bisogna
    # specificare il numero della porta (l'utente deve esserne a conoscenza). Mettendolo a costruttore facciamo sì che utente
    # definisca quale port userà.
    def __init__(self, port, peers=None):
        # se non trova altri peers all'inizio, crea un'iniziale set vuoto e lo aggiunge a costruttore
        if peers is None:
            peers = set()
        self.peers = {address(*peer) for peer in peers}
        # creo qua il nuovo socket per il peer e lo bindo alla porta (avra IP: "0.0.0.0" e port = numero di porta indicato)
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.bind(address(port=port)) # qui riserviamo la port scelta da utente

    # decoratore per recuperare il proprio end-point (tupla IP + Port)
    @property
    def local_address(self):
        return self.__socket.getsockname()
    
    # questo metodo prende in ingresso un messaggio (se è stringa, convertito in bytes) e la invia tramite
    # il metodo sendto il messaggio a tutti i peers che sono presenti nel set di peers che il peer corrente ha salvato
    def send_all(self, message):
        if not isinstance(message, bytes):
            message = message.encode()
        for peer in self.peers:
            self.__socket.sendto(message, peer)

    # questo metodo sfrutta il metodo socket.recvfrom per ricevere un messaggio e aggiunge alla lista di peers il messaggero
    # (sempre tupla IP + port)
    def receive(self):
        message, address = self.__socket.recvfrom(1024)
        self.peers.add(address)
        return message.decode(), address #restituisco il messaggio decodificato e l'indirizzo

    def close(self):
        self.__socket.close()


if __name__ == '__main__':
    assert address('localhost:8080') == ('localhost', 8080)
    assert address('127.0.0.1', 8080) == ('127.0.0.1', 8080)
    assert message("Hello, World!", "Alice", datetime(2024, 2, 3, 12, 15)) == "[2024-02-03T12:15:00] Alice:\n\tHello, World!"
