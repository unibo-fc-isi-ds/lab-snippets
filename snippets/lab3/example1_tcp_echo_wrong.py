from snippets.lab3 import address
import socket
import sys


mode = sys.argv[1].lower().strip()
BUFFER_SIZE = 1024


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
    port = int(sys.argv[2])
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(address(port=port)) 
        server.listen(1) # only one connection at a time
        print(f"# echo server listening on port {port}")
        sock, addr = server.accept()
        print(f"# start echoing data from {addr}")
        while True:
            buffer = sock.recv(BUFFER_SIZE)
            if not buffer:
                break
            sock.sendall(buffer)
            print(f"# echoed {len(buffer)} bytes: {buffer!r}", flush=True)
        sock.close()
    print("# connection closed")
