from datetime import datetime
import socket


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


def message(text: str, sender: str, timestamp: datetime=None):
    if timestamp is None:
        timestamp = datetime.now()
    return f"[{timestamp.isoformat()}] {sender}:\n\t{text}"


class Peer:
    def __init__(self, port, peers=None):
        if peers is None:
            peers = set()
        self.__peers = {address(*peer) for peer in peers}
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__socket.bind(address(port=port))

    @property
    def local_address(self):
        return self.__socket.getsockname()
    
    def send_all(self, message):
        if not isinstance(message, bytes):
            message = message.encode()
        for peer in self.__peers:
            self.__socket.sendto(message, peer)

    def receive(self):
        message, address = self.__socket.recvfrom(1024)
        self.add_peer(address)
        return message.decode(), address
    
    def add_peer(self, peer):
        self.__peers.add(address(*peer))

    def close(self):
        self.__socket.close()
