import pytest
import hypothesis.strategies as st
from hypothesis import given
import ipaddress
import string

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
        super().__init__("IP address must be a string and IPv4 type")



class Message():
    def __init__(self, message: str, internalMessage: bool = False):
        self.__message = message
        self.__internalMessage = internalMessage
    # Distinguere messaggi interni da messaggi esterni
    pass

class Peer():
    def send(self, message: Message):
        pass
    def receive(self) -> Message:
        pass
    def connect(self, peers: list['Peer']):
        pass
    def disconnect(self, peers: list['Peer']):
        pass
    
    # funzione privata periodica di controllo della rete

class Controller():
    def handleOutputMessage(self, message: Message):
        pass
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
    def test_ip_address_check_1(self, indirizzo_ip, porta):
        assert obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))
    
    # Invalid port values
    @given(indirizzo_ip=st.ip_addresses(v=4),
           porta=st.integers(min_value=65536, max_value=6553555))
    def test_ip_address_check_2(self, indirizzo_ip, porta):
        with pytest.raises(InvalidPortRange):
            obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))
    
    @given(indirizzo_ip=st.ip_addresses(v=4),
           porta=st.integers(min_value=-1235431, max_value=-1))
    def test_ip_address_check_3(self, indirizzo_ip, porta):
        with pytest.raises(InvalidPortRange):
            obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))

    # Invalid IPv6 address 
    @given(indirizzo_ip=st.ip_addresses(v=6),
           porta=st.integers(min_value=1, max_value=65535))
    def test_ip_address_check_4(self, indirizzo_ip, porta):
        with pytest.raises(InvalidIpAddress):
            obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))
    
    # Invalid ip address
    @given(indirizzo_ip=st.text(),
           porta=st.integers(min_value=1, max_value=65535))
    def test_ip_address_check_5(self, indirizzo_ip, porta):
        with pytest.raises(InvalidIpAddress):
            obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))

    # Valid ip address without port
    @given(indirizzo_ip=st.ip_addresses(v=4))
    def test_ip_address_check_6(self, indirizzo_ip):
        assert obtainIpaddressFromString(str(indirizzo_ip))

    # Invalid ip address without port
    @given(indirizzo_ip=st.ip_addresses(v=6))
    def test_ip_address_check_7(self, indirizzo_ip):
        with pytest.raises(InvalidIpAddress):
            obtainIpaddressFromString(str(indirizzo_ip))

    # Invalid port, because is not an integer
    @given(indirizzo_ip=st.ip_addresses(v=4),
           porta=st.text(alphabet=string.ascii_letters + string.punctuation))
    def test_ip_address_check_8(self, indirizzo_ip, porta):
        with pytest.raises(InvalidIpAddress):
            obtainIpaddressFromString(str(indirizzo_ip)+ ":" + str(porta))