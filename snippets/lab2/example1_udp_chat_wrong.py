from snippets.lab2 import *
import sys

#creato qui un Peer, passandogli da terminale la port e (in caso) una lista di tutti i peers
peer = Peer(
    port = int(sys.argv[1]),
    peers = [address(peer) for peer in sys.argv[2:]]
)

print(f'Bound to: {peer.local_address}') # mostra qui l'indirizzo locale
print(f'Local IP addresses: {list(local_ips())}') # e la lista di tutti gli IP locali
username = input('Enter your username to start the chat:\n')
while True: #qui fa in modo che i messaggi vengano propagati nel network, per poi stampare quello che riceve
    content = input('> ')
    peer.send_all(message(content, username))
    print(peer.receive()[0])
    # errore in questo esempio: assumo che dopo aver inviato un messaggio, mi aspetto che vi sia un solo messaggio da ricevere
    # mi sto immaginando che conversazione sia: messaggio -> risposta -> messaggio -> risposta...
    # ricevere in questo caso è un'operazione bloccante, così come inviare (dopo aver ricevuto una volta, blocca altre
    # ricevute in attesa che io mandi una nuova risposta)
    # Problemi anche nel terminare, il fatto che uno agisce da server e uno da client...
