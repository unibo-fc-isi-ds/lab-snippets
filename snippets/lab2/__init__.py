from datetime import datetime
import psutil
import socket

# Used to split the address in ip and port
def address(ip='0.0.0.0:0', port=None):
    ip = ip.strip()
    if ':' in ip:
        ip, p = ip.split(':')
        p = int(p)
        port = port or p
    if port is None:
        port = 0
    assert port in range(0, 65536), "Port number must be in the range 0-65535"
    assert isinstance(ip, str), "IP address must be a string"
    return ip, port

# Used just to print the message in a pretty way
def message(text: str, sender: str, timestamp: datetime=None):
    if timestamp is None:
        timestamp = datetime.now()
    return f"[{timestamp.isoformat()}] {sender}:\n\t{text}"

# Gets all the ips of the local machine
def local_ips():
    for interface in psutil.net_if_addrs().values():
        for addr in interface:
            if addr.family == socket.AF_INET:
                    yield addr.address


class Peer:
    # Initialises the peer, reserving the port and adding the peers (if any)
    def __init__(self, port, peers=None):
        if peers is None:
            peers = set()
        self.peers = {address(*peer) for peer in peers}
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.bind(address(port=port))

    @property # Read-only property to get the local endpoint (ip:port)
    def local_address(self):
        return self.__socket.getsockname()
    
    # Sends a message to all the peers
    def send_all(self, message):
        if not isinstance(message, bytes):
            message = message.encode()
        for peer in self.peers:
            self.__socket.sendto(message, peer)

    # Receives a message from a peer (BLOCKING), keeping track of the peer if new
    def receive(self):
        message, address = self.__socket.recvfrom(1024)
        self.peers.add(address)
        return message.decode(), address

    # Closes the socket (releasing the port)
    def close(self):
        self.__socket.close()


if __name__ == '__main__':
    assert address('localhost:8080') == ('localhost', 8080)
    assert address('127.0.0.1', 8080) == ('127.0.0.1', 8080)
    assert message("Hello, World!", "Alice", datetime(2024, 2, 3, 12, 15)) == "[2024-02-03T12:15:00] Alice:\n\tHello, World!"
