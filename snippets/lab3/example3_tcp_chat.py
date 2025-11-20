from snippets.lab3 import *
import sys

mode = sys.argv[1].lower().strip() #primo argomento: specifica se sono in modalità client o server
remote_peer: Client | None = None 

#gestione dell'invio di un messaggio
def send_message(msg, sender):
    if remote_peer is None: # nessun peer connesso
        print("No peer connected, message is lost")
    elif msg: #c'è un peer connesso e il messaggio non è vuoto
        remote_peer.send(message(msg.strip(), sender))
    else: #c'è un peer connesso ma il messaggio è vuoto
        print("Empty message, not sent")

#callback del server per la gestione dei messaggi ricevuti
def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(payload)
        case 'close':
            print(f"Connection with peer {connection.remote_address} closed")
            global remote_peer #cambio il valore della variabile globale
            remote_peer = None #non c'è più nessun peer connesso
        case 'error':
            print(error)

#se ho avviato in modalità server, avvio il server e aspetto connessioni in ingresso
if mode == 'server':
    port = int(sys.argv[2])

    #callback del server per la gestione delle nuove connessioni
    def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {address[0]} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Open ingoing connection from: {address}")
                connection.callback = on_message_received #setto la callback per la connessione
                global remote_peer #cambio il valore della variabile globale
                remote_peer = connection #qui c'è il problema
            case 'stop':
                print(f"Stop listening for new connections")
            case 'error':
                print(error)

    server = Server(port, on_new_connection)
#se sono in modalità client, mi connetto al server specificato
elif mode == 'client':
    remote_endpoint = sys.argv[2] #estraggo ip e porta del server a cui connettermi

    remote_peer = Client(address(remote_endpoint), on_message_received)
    print(f"Connected to {remote_peer.remote_address}")


username = input('Enter your username to start the chat:\n')
print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
while True:
    try:
        content = input() #leggo da stdin il messaggio da inviare
        send_message(content, username) #invio il messaggio
    except (EOFError, KeyboardInterrupt): #eccezioni : ctrl+D o ctrl+C
        if remote_peer: #se c'è un peer connesso
            remote_peer.close() #chiudo la connessione
        break 
if mode == 'server':
    server.close()