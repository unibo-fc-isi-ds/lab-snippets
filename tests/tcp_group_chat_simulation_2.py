from snippets.lab3.exercise_tcp_group_chat import TCPPeer
from snippets.lab3 import clear_log_file
import time
import unittest

LOG_FILE = './tests/chat_log.log'
DESIRED_FILE = './tests/simulation_2_desired.txt'

class TestPeerDisconnection(unittest.TestCase):
     
     def setUp(self):
        clear_log_file(LOG_FILE)
        self.peer_0 = TCPPeer(username='User0', port=8080, remote_endpoints=None)
        self.peer_1 = TCPPeer(username='User1', port=8081, remote_endpoints=['localhost:8080'])
        self.peer_2 = TCPPeer(username='User2', port=8082, remote_endpoints=['localhost:8080','localhost:8081'])
        self.peer_3 = TCPPeer(username='User3', port=8083, remote_endpoints=['localhost:8080','localhost:8081','localhost:8082'])
     
     def test_disconnection(self):
        time.sleep(3)
        self.peer_0.send_message("Bye! I'm leaving")
        time.sleep(3)
        self.peer_0.close()
        time.sleep(5)
        self.peer_1.send_message("Hey all!")
        time.sleep(3)
        # ! TODO: compare output with desire behavior
        self.assertTrue(1,1)
     
     def tearDown(self):
        self.peer_1.close()
        time.sleep(5)
        self.peer_2.close()
        time.sleep(5)
        self.peer_3.close()