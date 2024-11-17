import threading
import pytest
import hypothesis.strategies as st
from hypothesis import given
import ipaddress
import string
import socket
import sys
import json

# Functions
def validateIpAddress(ip: str):
    try:
        value = ipaddress.ip_address(ip)
        return isinstance(value, ipaddress.IPv4Address)
    except ValueError:
        return False
    
# Copied from __init__ lab3
# Added check on ':' char, because accepted only x.x.x.x or x.x.x.x:p
# Can raise InvalideIpAddress or InvalidPortRange
def obtainIpaddressFromString(ip='0.0.0.0:0', port=None):
    ip = ip.strip()
    if ip.count(':') != 1 and ip.count(':') != 0:
        raise InvalidIpAddress
    if ':' in ip:
        ip, p = ip.split(':')
        try:
            p = int(p)
        except ValueError:
            raise InvalidIpAddress
        port = port or p
    if port is None:
        port = 0
    if (port not in range(0, 65536)):
        raise InvalidPortRange
    if (not isinstance(ip, str) or not validateIpAddress(ip)):
        raise InvalidIpAddress
    return ip, port



class InvalidPortRange(Exception):
    def __init__(self):
        super().__init__("Port number must be in the range 0-65535")

class InvalidIpAddress(Exception):
    def __init__(self):
        super().__init__("Invalid IP address, must be a string (x.x.x.x:p or x.x.x.x) and IPv4 type")

class InvalidMessage(Exception):
    def __init__(self):
        super().__init__("Message args are not correct")



# Class dict -> Encoded data str (JSON), Encoded data str -> dict
class Message():
    def __init__(self, values):
        try:
            self.originalData = self.__Dictmethod(values)
            self.encodedData = self.__JSONmethod(values)
        except ValueError:
            raise InvalidMessage()
        
    def __JSONmethod(self, values):
        if (isinstance(values, str)):
            return values
        elif (isinstance(values, dict)):
            return self.__DicttoJSON(values)
        else:
            raise InvalidMessage()
        
    def __Dictmethod(self, values):
        if (isinstance(values, dict)):
            return values
        elif (isinstance(values, str)):
            return self.__JSONtoDict(values)
        else:
            raise InvalidMessage()

    def __JSONtoDict(self, JSONstring):
        return json.loads(JSONstring)
    
    def __DicttoJSON(self, dictionary):
        return json.dumps(dictionary)



# Può essere utile avere uno strumento di log
class Peer():
    def __init__(self, port: int, peers=None):
        self.__set_peers(peers)
        self.__thread = []
        self.__conn = []
        self.__observer = []

        try:
            self.__set_server(port)
        except KeyboardInterrupt:
            for thread in self.__thread:
                thread.join()
            self.close()
            print("\nSocket server chiuso")
            sys.exit(0)
            
    def send(self, message: Message):
        pass

    def receive(self,conn,addr):
        while True:
            message = conn.recv(2048) 
            message_str = message.decode('utf-8')
            self.notify(message_str)
            
    def addObserver(self, observer):
        self.__observer.append(observer)

    def notify(self, message):
        for singleObserver in self.__observer:
            singleObserver.handleOutputMessage(message)

    def connect(self, peers: list['Peer']):
        pass
    def disconnect(self, peers: list['Peer']):
        pass

    def close(self):
        if self.__socket:
            self.__socket.close()

    def __set_server(self, port):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.__socket.bind(obtainIpaddressFromString('127.0.0.1', port=port))
        except (InvalidPortRange, InvalidIpAddress) as e:
            print(f"Error: {e}")
            sys.exit(1)
        self.__socket.listen(100)
        while True:
            conn, addr = self.__socket.accept()  # Accept a client connection
            self.__conn.append(conn)
            thread = threading.Thread(target=self.receive, args=(conn, addr))
            self.__thread.append(thread)
            thread.start()  # Start a new thread for each client
            print(f"Active connections: {threading.activeCount() - 1}")

    def __set_peers(self, peers):
        if peers is None:
            peers = set()
        try:
            self.peers = {obtainIpaddressFromString(*peer) for peer in peers}
        except (InvalidPortRange, InvalidIpAddress) as e:
            print(f"Error: {e}")
            sys.exit(1)
    
    # funzione privata periodica di controllo della rete


class Controller():
    def handleOutputMessage(self, message):
        print(message)
    def handleInputMessage(self, message: Message):
        pass

class View():
    def outputMessage(self, message: str):
        pass
    def inputMessage(self) -> str:
        pass



class Test():
    # Those test check ip address and port
    # Valid "x.x.x.x:port" format
    @given(indirizzo_ip=st.ip_addresses(v=4),
           porta=st.integers(min_value=1, max_value=65535))
    def test_IpAddressValidFormat(self, indirizzo_ip, porta):
        assert obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))
    
    # Invalid port values
    @given(indirizzo_ip=st.ip_addresses(v=4),
           porta=st.integers(min_value=65536, max_value=6553555))
    def test_IpAddressInvalidPortValue1(self, indirizzo_ip, porta):
        with pytest.raises(InvalidPortRange):
            obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))
    
    @given(indirizzo_ip=st.ip_addresses(v=4),
           porta=st.integers(min_value=-1235431, max_value=-1))
    def test_IpAddressInvalidPortValue2(self, indirizzo_ip, porta):
        with pytest.raises(InvalidPortRange):
            obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))

    # Invalid IPv6 address 
    @given(indirizzo_ip=st.ip_addresses(v=6),
           porta=st.integers(min_value=1, max_value=65535))
    def test_IpAddressInvalidIPv6(self, indirizzo_ip, porta):
        with pytest.raises(InvalidIpAddress):
            obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))
    
    # Invalid ip address
    @given(indirizzo_ip=st.text(),
           porta=st.integers(min_value=1, max_value=65535))
    def test_IpAddressInvalidAddress(self, indirizzo_ip, porta):
        with pytest.raises(InvalidIpAddress):
            obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))

    # Valid ip address without port
    @given(indirizzo_ip=st.ip_addresses(v=4))
    def test_IpAddressValidAddressWoutPort(self, indirizzo_ip):
        assert obtainIpaddressFromString(str(indirizzo_ip))

    # Invalid ip address without port
    @given(indirizzo_ip=st.ip_addresses(v=6))
    def test_IpAddressInvalidAddressWoutPort(self, indirizzo_ip):
        with pytest.raises(InvalidIpAddress):
            obtainIpaddressFromString(str(indirizzo_ip))

    # Invalid port, because is not an integer
    @given(indirizzo_ip=st.ip_addresses(v=4),
           porta=st.text(alphabet=string.ascii_letters + string.punctuation))
    def test_IpAddressInvalidPortNotInteger(self, indirizzo_ip, porta):
        with pytest.raises(InvalidIpAddress):
            obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))


    # Valid Message from dict
    @given(nome1 = st.text(alphabet=string.ascii_letters + string.punctuation),
           nome2 = st.text(alphabet=string.ascii_letters + string.punctuation),
           valore1 = st.text(),
           valore2 = st.text())
    def test_MessageValidFromDict(self, nome1, nome2, valore1, valore2):
        testDict = {nome1: valore1, nome2: valore2}
        ms = Message(testDict)
        assert ms.originalData == testDict
        assert isinstance(ms.originalData, dict)

    # None args
    def test_MessageInvalidNoneArgs(self):
        with pytest.raises(InvalidMessage):
            assert Message(None)

    # Invalid Type Args
    def test_MessageInvalidListArgs(self):
        with pytest.raises(InvalidMessage):
            assert Message(list())

    # Valid Message from json
    @given(nome1 = st.text(alphabet=string.ascii_letters + string.punctuation),
           nome2 = st.text(alphabet=string.ascii_letters + string.punctuation),
           valore1 = st.text(),
           valore2 = st.text())
    def test_MessageValidFromJSON(self, nome1, nome2, valore1, valore2):
        testDict = {nome1: valore1, nome2: valore2}
        jsonString = json.dumps(testDict)
        ms = Message(jsonString)
        assert ms.encodedData == jsonString
        assert isinstance(ms.encodedData, str)

    @given(valore = st.text(alphabet=string.ascii_letters + string.punctuation))
    def test_MessageInvalidString(self, valore):
        with pytest.raises(InvalidMessage):
            assert Message(valore)






""" class Client:
    def __init__(self, host, port):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
    def invia_messaggi(self):
        self.client.connect((self.host, self.port))
        time.sleep(2)
        strl= 'Carlo $ Ciao'
        self.client.send(strl.encode('utf-8'))
        time.sleep(2)
        strl= 'Carlo $ Ciao2'
        self.client.send(strl.encode('utf-8'))
        time.sleep(2)
        strl= 'Carlo $ $$$EXIT'
        self.client.send(strl.encode('utf-8'))
        self.client.close()

    def start(self):
        
        print("Ciao")
        invia_thread = threading.Thread(target=self.invia_messaggi)
        invia_thread.start()
        invia_thread.join()

import time

if __name__=='__main__':
    cl = Client('127.0.0.1',8080)
    cl_thread = threading.Thread(target=cl.start)
    cl_thread.start()
    peer = Peer(int(sys.argv[1]), None)
    cl_thread.join()
 """