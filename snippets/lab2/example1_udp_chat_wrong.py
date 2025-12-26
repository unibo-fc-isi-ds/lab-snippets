from snippets.lab2 import *
import sys


peer = Peer(
    port = int(sys.argv[1]),
    peers = [address(peer) for peer in sys.argv[2:]]
)

print(f'Bound to: {peer.local_address}')
print(f'Local IP addresses: {list(local_ips())}')
username = input('Enter your username to start the chat:\n')
while True:
    content = input('> ') #problema 1 -legge il messaggio da inviare (operazione bloccante) --> soluzione: multithreading per gestire l'input
    peer.send_all(message(content, username))
    print(peer.receive()[0]) #problema 2 - riceve e stampa il messaggio in arrivo (operazione bloccante)

#problema 3 : i partecipanti agiscono come peer, ma in realtà unoagisce come client (deve sapere l'indirizzo IP e la porta degli altri peer per inviare messaggi) 
#             gli altri come server (ascoltano i messaggi in arrivo) --> soluzione : implementare un broker

#problema 4 : il programma non gestisce la chiusura pulita della connessione UDP (ad esempio con Ctrl+C) --> soluzione: gestire le eccezioni e chiudere il socket correttamente

#problema 5 : non c'è nessun meccanismo di autenticazione (un peer può fingersi un altro peer semplicemente usando il suo nome utente)
#  --> soluzione: implementare un sistema di autenticazione (ad esempio con chiavi pubbliche/private) non è lo scopo del corso

#problema 6 : UDP è un protocollo non affidabile (i messaggi possono andare persi, arrivare duplicati o fuori ordine)
#  --> soluzione: implementare meccanismi di retry o implementare protocollo TCP

#example2_udp_chat.py risolve alcuni di questi problemi
