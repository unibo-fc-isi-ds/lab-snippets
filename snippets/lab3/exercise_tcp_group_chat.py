import os, threading, pytest, ipaddress, string, socket, sys, json, logging, time, psutil
import hypothesis.strategies as st
from hypothesis import given

# Function taken from __init__ lab2
def local_ips():
    for interface in psutil.net_if_addrs().values():
        for addr in interface:
            if addr.family == socket.AF_INET:
                    yield addr.address

def validateIpAddress(ip: str):
    try:
        value = ipaddress.ip_address(ip)
        return isinstance(value, ipaddress.IPv4Address)
    except ValueError:
        return ip == 'localhost'
    
# Function taken from __init__ lab3
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
    if (not isinstance(ip, str)):
        raise InvalidIpAddress("Ip is not a string")
    if (not validateIpAddress(ip)):
        raise InvalidIpAddress
    if (ip == 'localhost'):
        ip = '127.0.0.1'
    return ip, port


# Exceptions
class InvalidPortRange(Exception):
    def __init__(self, message: str = None):
        if (isinstance(message,str) and message != None):
            super().__init__(message)
        else:
            super().__init__("Port number must be in the range 0-65535")

class InvalidIpAddress(Exception):
    def __init__(self, message: str = None):
        if (isinstance(message,str) and message != None):
            super().__init__(message)
        else:
            super().__init__("Invalid IP address, must be a string (x.x.x.x:p or x.x.x.x) and IPv4 type")

class InvalidMessage(Exception):
    def __init__(self, message: str = None):
        if (isinstance(message,str) and message != None):
            super().__init__(message)
        else:
            super().__init__("Message args are not correct")

class ImpossibleToConnectToPeer(Exception):
    def __init__(self, message: str = None):
        if (isinstance(message,str) and message != None):
            super().__init__(message)
        else:
            super().__init__("Impossible to connect with the peer")

class PeerNotExpectedDisconection(Exception):
    def __init__(self, message: str = None):
        if (isinstance(message,str) and message != None):
            super().__init__(message)
        else:
            super().__init__("Peer disconnected unexpectedly")


# Class dict -> Encoded data str (JSON), Encoded data str -> dict
class Message():
    def __init__(self, values):
        try:
            self.originalData = self.__Dictmethod(values)
            self.encodedData = self.__JSONmethod(values)
            self.messageLen = len(self.encodedData)
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


class Peer():
    LOG_FILE_NAME = "peer.log"
    BUFFER_SIZE = 2048
    CLOSED_CONNECTION_REQUEST = "$$$EXIT"
    NEW_CONNECTION_REQUEST = "$$$NEWCONNECT"
    CHECK_CONNECTION_REQUEST = "$$$CHECK"
    SELF_IP_ADDRESS = "127.0.0.1"
    MAX_NUMBER_LISTENER = 100
    APP_NAME = "TCP Group Chat"
    SECONDS_BETWEEN_CHECKS = 5

    def __init__(self, ip: str, port: int, peers = None, log: bool = False):
        self.__thread = []
        self.__observer = []
        self.__logger = log
        self.port = port
        self.username = None
        self.__connections = {}
        self.ip = ip

        self.__startLogger()

        try:
            self.ip, _ = obtainIpaddressFromString(self.ip)
            if self.ip not in list(local_ips()):
                self.__logError("Ip in args is not compatible")
                sys.exit(1)
        except (InvalidIpAddress):
            self.__logError("There is no ip in args")
            sys.exit(1)
        
        self.__set_peers(peers)
        self.__logInfo("Peers: " + str(self.peers))

    def start(self):        
        self.server_thread = threading.Thread(target=self.__serverStart, args=([self.port]))
        self.server_thread.daemon = True
        self.server_thread.start()
        self.__connectToAllPeers()

        self.check_connections = threading.Thread(target=self.__checkPeerConnections, args=([]))
        self.check_connections.daemon = True
        self.check_connections.start()

    def inputUsername(self, name: str):
        self.username = name

    def sendToEveryone(self, message: str):
        notReacheablePeers = []
        for (ip, port), _ in self.__connections.items():
            try:
                self.send(ip, port, message)
            except PeerNotExpectedDisconection:
                notReacheablePeers.append((ip, port))
        for ip, port in notReacheablePeers:
            self.disconnect(ip, port)
            
    def send(self, ip: str, port: int, message: str):
        if (len(message) >= self.BUFFER_SIZE):
            self.__logError("Length of the message is more than the buffer size. Cannot send.")
            data = {
                "username": self.APP_NAME,
                "message": "Length of the message is more than the buffer size. Cannot send."
            }
            self.notify(Message(data))
            return
        try:
            self.__connections[(ip, port)].sendall(bytes(message, 'utf-8'))
            self.__logInfo("Send message <" + message + "> to " + ip + ":" + str(port))
        except socket.error as e:
            self.__logError("The connection is failed with ip: " + ip + " port: " + str(port) + str(e))
            data = {
                "username": self.APP_NAME,
                "message": "Peer ip: " + ip + " port: " + str(port) + " is unrichable. Disconnected."
            }
            self.notify(Message(data))
            raise PeerNotExpectedDisconection()
        except Exception as e:
            self.__logError("Error send message: " + str(e))

    def receive(self, conn):
        while True:
            message = conn.recv(self.BUFFER_SIZE).decode('utf-8')
            if (len(message) > 0):
                self.__logInfo("Received message <" + message + "> from ip: " 
                            + str(conn.getpeername()[0]) + " port: " + str(conn.getpeername()[1]))
                m = Message(message)
                self.notify(m)
                if(self.__isCloseConnectionMessage(m.originalData["message"])):
                    self.__logInfo("Closed connection with: " + m.originalData["serverIP"] + ":" +str(m.originalData["serverPort"]))
                    self.disconnect(m.originalData["serverIP"], m.originalData["serverPort"])
                    return
                if(self.__isNewConnectionMessage(m)):
                    self.__acceptNewConnection(m)

    # Pattern observer for controller     
    def addObserver(self, observer):
        self.__observer.append(observer)

    def notify(self, message):
        for singleObserver in self.__observer:
            singleObserver.handleOutputMessage(message)

    def connect(self, ip: str, port: int):
        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            client.connect((ip, port))
            self.__connections[(ip, port)] = client
            self.send(ip, port, Message(self.__newConnectionMessage()).encodedData)
            self.__logInfo("Connected with ip: " + ip + " port: " + str(port))
        except OSError:
            self.__logError("Can not connect with ip: " + ip + " port: " + str(port))
            data = {
                "username": self.APP_NAME,
                "message": "Impossible to connect with ip: " + ip + " port: " + str(port)
            }
            self.notify(Message(data))

    # Disconnect a single connection      
    def disconnect(self, ip: str, port: int):
        self.__connections[(ip, port)].close()
        del self.__connections[(ip, port)]

    # Close all sockets
    def close(self):
        for (ip, port), value in self.__connections.items():
            self.send(ip, port, Message(self.__disconnectionMessage()).encodedData)
            self.__connections[(ip, port)].close()
            self.__logInfo("Closed connection with: " + ip + ":" +str(port))
        if self.__socket:
            self.__socket.close()

    def __connectToAllPeers(self):
        for addr, port in self.peers:
            addr, port = obtainIpaddressFromString(addr, port)
            self.connect(addr, port)

    def __newConnectionMessage(self):
        return {
            "serverIP": self.ip,
            "serverPort": self.port,
            "username": self.username if self.__isUsernameSet() 
                else (self.ip + ":" + str(self.port)),
            "message": self.NEW_CONNECTION_REQUEST
        }
    
    def __disconnectionMessage(self):
        return {
            "serverIP": self.ip,
            "serverPort": self.port,
            "username": self.username if self.__isUsernameSet() 
                else (self.ip + ":" + str(self.port)),
            "message": self.CLOSED_CONNECTION_REQUEST
        }

    def __acceptNewConnection(self, message: Message):
        ip, port = obtainIpaddressFromString(message.originalData["serverIP"], 
                                               port = message.originalData["serverPort"])
        self.connect(ip, port)

    # Check if the connection request is already present
    def __isNewConnectionMessage(self, message: Message):
        return message.originalData["message"] == self.NEW_CONNECTION_REQUEST and not ((message.originalData["serverIP"], message.originalData["serverPort"]) in self.__connections)

    def __isCloseConnectionMessage(self, message):
        return message == self.CLOSED_CONNECTION_REQUEST

    # Different thread for server
    def __serverStart(self, port):
        try:
            self.server_thread = threading.Thread(target=self.__set_server, args=([port]))
            self.server_thread.daemon = True
            self.server_thread.start()
            self.server_thread.join()
        except KeyboardInterrupt:
            for thread in self.__thread:
                thread.join()
            self.close()
            self.__logInfo("Server socket closed")
            os._exit(0)

    def __set_server(self, port):
        self.__socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.__socket.bind(obtainIpaddressFromString(self.SELF_IP_ADDRESS, port=port))
        except (InvalidPortRange, InvalidIpAddress) as e:
            self.__logError(e)
            print(str(e) + ". Restart the app with different port")
            os._exit(1)
        except (OSError):
            self.__logError("Address already in use")
            print("Address already in use. Restart the app with different port")
            os._exit(1)
        self.__socket.listen(self.MAX_NUMBER_LISTENER)
        # Loop for connections accept
        while True:
            conn, _ = self.__socket.accept()  # Accept a client connection
            thread = threading.Thread(target=self.receive, args=([conn]))
            thread.daemon = True
            self.__thread.append(thread)
            thread.start()  # Start a new thread for each client
            self.__logInfo("New connection active from ip: " + str(conn.getpeername()[0]) + " port: " + str(conn.getpeername()[1]))

    # Take from args peers and save in self.__peers
    def __set_peers(self, peers):
        if peers is None:
            peers = set()
        try:
            self.peers = {obtainIpaddressFromString(peer) for peer in peers}
        except (InvalidPortRange, InvalidIpAddress) as e:
            self.__logError(e)
            sys.exit(1)

    def __logError(self, message):
        if (self.__logger):
                self.__logger.error((str(self.port) if not self.__isUsernameSet() 
                                else "{"+self.username+"} ") + message)
                
    def __logInfo(self, message):
        if (self.__logger):
                self.__logger.info((str(self.port) if not self.__isUsernameSet() 
                                else "{"+self.username+"} ") + message)
                
    def __isUsernameSet(self):
        if (self.username == None):
            return False
        else:
            return True
    
    def __startLogger(self):
        if (self.__logger):
            logging.basicConfig(filename=(self.ip+":"+str(self.port)+".log"),
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    filemode='w')
            self.__logger = logging.getLogger()
            self.__logger.setLevel(logging.DEBUG)
    
    # Loop with message check
    def __checkPeerConnections(self):
        while True:
            time.sleep(self.SECONDS_BETWEEN_CHECKS)
            self.sendToEveryone(Message(self.__checkPeerMessage()).encodedData)

    # Create message for check peers
    def __checkPeerMessage(self):
        return {
            "username": self.username,
            "message": self.CHECK_CONNECTION_REQUEST
        }


class Controller():
    def __init__(self, args):
        self.__observer = []
        self.__peer = Peer(args[1], int(args[2]), peers=args[3:], log=True)
        self.__peer.addObserver(self)
        self.addObserver(self.__peer)
        
        self.___inputUsername()
        print('\nType your message and press Enter to send it. Messages from other peers will be displayed below.\n')

        time.sleep(1)
        self.__peer.start()
        
    # Main loop for input
    def start(self):
        try:
            while True:
                content = input()
                data = {
                    "username": self.__username,
                    "message": content
                }
                self.handleInputMessage(Message(data))
        except KeyboardInterrupt:
            self.__peer.close()

    # Pattern Observer
    def addObserver(self, observer):
        self.__observer.append(observer)

    def handleOutputMessage(self, message: Message):
        match message.originalData["message"]:
            case self.__peer.NEW_CONNECTION_REQUEST:
                print("<" + message.originalData["username"] + ">: Join the chat")
            case self.__peer.CLOSED_CONNECTION_REQUEST:
                print("<" + message.originalData["username"] + ">: Left the chat")
            case self.__peer.CHECK_CONNECTION_REQUEST:
                # Check if peer is alive
                pass
            case _:
                print("<" + message.originalData["username"] + ">: " + message.originalData["message"])

    def handleInputMessage(self, message: Message):
        for singlebserver in self.__observer:
            singlebserver.sendToEveryone(message.encodedData)

    def ___inputUsername(self):
        print("\nEnter your username to start the chat: ")
        self.__username = input()
        self.__peer.inputUsername(self.__username)


if __name__=='__main__':
    c = Controller(sys.argv)
    c.start()



class Test():

    # Controller class only for testing use
    class Testing_Controller(Controller):
        __test__ = False
        def __init__(self, args, name = "Default"):
            self.__observer = []
            self.peer = Peer(args[0], int(args[1]), peers=args[2:], log=False)
            self.peer.addObserver(self)
            self.addObserver(self.peer)
            self.solution= []
            
            self.peer.inputUsername(name)

            time.sleep(0.5)
            self.peer.start()

        def handleOutputMessage(self, message: Message):
            match message.originalData["message"]:
                case self.peer.NEW_CONNECTION_REQUEST:
                    self.solution.append((message.originalData["username"], self.peer.NEW_CONNECTION_REQUEST))
                case self.peer.CLOSED_CONNECTION_REQUEST:
                    self.solution.append((message.originalData["username"], self.peer.CLOSED_CONNECTION_REQUEST))
                case self.peer.CHECK_CONNECTION_REQUEST:
                    pass
                case _:
                    self.solution.append((message.originalData["username"], message.originalData["message"]))

        def handleInputMessage(self, message: Message):
            for singlebserver in self.__observer:
                singlebserver.sendToEveryone(message.encodedData)
        
        def close(self):
            self.peer.close()

        def addObserver(self, observer):
            self.__observer.append(observer)

        def getResult(self):
            return self.solution

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

    # Test localhost string
    def test_IpAddressValidLocalhost(self):
        assert obtainIpaddressFromString('localhost:8080')


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

    # Check too long messange

    def test_longMessagePeer(self):
        controller1 = self.Testing_Controller(["localhost", "8080"])
        controller2 = self.Testing_Controller(["localhost", "8081", "localhost:8080"])
        time.sleep(0.5)
        long_string = 'a'*(Peer.BUFFER_SIZE)
        data = {
            "username": "Default",
            "message": long_string
        }
        controller1.handleInputMessage(Message(data))
        data = {
            "username": "Default",
            "message": 0
        }
        controller2.handleInputMessage(Message(data))
        time.sleep(0.5)
        controller1.close()
        time.sleep(0.5)
        controller2.close()

        expected_result = []
        expected_result.append(("Default", Peer.NEW_CONNECTION_REQUEST))
        expected_result.append(('TCP Group Chat', 'Length of the message is more than the buffer size. Cannot send.'))
        expected_result.append(("Default", 0))

        assert expected_result == controller1.getResult()

        expected_result = []
        expected_result.append(("Default", Peer.NEW_CONNECTION_REQUEST))
        expected_result.append(("Default", Peer.CLOSED_CONNECTION_REQUEST))

        assert expected_result == controller2.getResult()

    # Normal Peer connection
    def test_normalPeer(self):
        controller1 = self.Testing_Controller(["localhost", "8082"])
        controller2 = self.Testing_Controller(["localhost", "8083", "localhost:8082"])
        time.sleep(0.5)
        long_string = 'a'*(Peer.BUFFER_SIZE-50)
        data = {
            "username": "Default",
            "message": long_string
        }
        controller1.handleInputMessage(Message(data))
        data = {
            "username": "Default",
            "message": 0
        }
        controller2.handleInputMessage(Message(data))
        time.sleep(0.5)
        controller1.close()
        time.sleep(0.5)
        controller2.close()

        expected_result = []
        expected_result.append(("Default", Peer.NEW_CONNECTION_REQUEST))
        expected_result.append(("Default", 0))

        assert expected_result == controller1.getResult()

        expected_result = []
        expected_result.append(("Default", Peer.NEW_CONNECTION_REQUEST))
        expected_result.append(("Default", long_string))
        expected_result.append(("Default", Peer.CLOSED_CONNECTION_REQUEST))

        assert expected_result == controller2.getResult() 

    # Simulate a disconection
    def test_disconectionPeer(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(('localhost',8087))
        sock.listen(1)

        controller2 = self.Testing_Controller(["localhost", "8086", "localhost:8087"])
        time.sleep(0.5)
        sock.close()

        time.sleep(10)
        controller2.close()
        time.sleep(0.1)

        expected_result = []
        expected_result.append(('TCP Group Chat','Peer ip: 127.0.0.1 port: 8087 is unrichable. Disconnected.'))

        assert expected_result == controller2.getResult()