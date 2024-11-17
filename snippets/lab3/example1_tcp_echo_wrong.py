from snippets.lab3 import address
import socket
import sys


mode = sys.argv[1].lower().strip() # prima verifico se sta entrando il server o il client
BUFFER_SIZE = 1024 # dimensione del buffer che riceve


if mode == 'client':
    remote_endpoint = address(sys.argv[2])
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(address()) # any port is fine
    sock.connect(remote_endpoint)
    print(f"# connected to {remote_endpoint}")
    while True:
        buffer = sys.stdin.buffer.read(BUFFER_SIZE)
        if not buffer:
            break
        sock.sendall(buffer)
    sock.shutdown(socket.SHUT_WR) # tells the server the client is done sending
    while True:
        buffer = sock.recv(BUFFER_SIZE)
        if not buffer:
            break
        sys.stdout.buffer.write(buffer)
        sys.stdout.buffer.flush()
    sock.close()
    print("# connection closed")
elif mode == 'server':
    port = int(sys.argv[2]) # qui specifico la porta da passare al server a linea di comando
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server: # viene creato il socket server
        server.bind(address(port=port)) # che viene bindato alla porta passata (con indirizzo IP "0.0.0.0")
        server.listen(1) # ascolta solo una connessione alla volta
        print(f"# echo server listening on port {port}")
        sock, addr = server.accept() # il server aspetta che venga stabilita una connessione e si bloccherà qui
        # quando un cliente riesce a contattare il server, il server legge un chunk di bytes di dimensione fissa del client
        # e poi rinvia tutto al client
        print(f"# start echoing data from {addr}")
        while True:
            buffer = sock.recv(BUFFER_SIZE)
            if not buffer:
                break
            sock.sendall(buffer)
            print(f"# echoed {len(buffer)} bytes: {buffer!r}", flush=True)
        sock.close()
    print("# connection closed")
