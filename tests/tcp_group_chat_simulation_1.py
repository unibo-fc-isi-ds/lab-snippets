from snippets.lab3.exercise_tcp_group_chat import TCPPeer
from snippets.lab3 import clear_log_file
import time
import unittest

LOG_FILE = './tests/chat_log.log'
DESIRED_FILE = './tests/simulation_1_desired.txt'

def compare_files(file1_path, file2_path):
    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        file1_lines = file1.readlines()
        file2_lines = file2.readlines()

    file1_lines = sorted([line.strip() for line in file1_lines])
    file2_lines = sorted([line.strip() for line in file2_lines])

    return file1_lines == file2_lines

class TestAllPeersReceiveMessages(unittest.TestCase):

    def setUp(self):
        clear_log_file(LOG_FILE)
        self.peer_0 = TCPPeer(username='User0', port=8080, remote_endpoints=None)
        self.peer_1 = TCPPeer(username='User1', port=8081, remote_endpoints=['localhost:8080'])
        self.peer_2 = TCPPeer(username='User2', port=8082, remote_endpoints=['localhost:8080','localhost:8081'])
        self.peer_3 = TCPPeer(username='User3', port=8083, remote_endpoints=['localhost:8080','localhost:8081','localhost:8082'])

    def test_send_message(self):
        self.peer_0.send_message("Hello!")
        time.sleep(3)
        self.peer_1.send_message("Hey!")
        time.sleep(3)
        self.peer_2.send_message("Howdy!")
        time.sleep(3)
        self.peer_3.send_message("Ciao!")
        time.sleep(3)
        self.assertTrue(compare_files(LOG_FILE, DESIRED_FILE))

    def tearDown(self):
        self.peer_0.close()
        time.sleep(5)
        self.peer_1.close()
        time.sleep(5)
        self.peer_2.close()
        time.sleep(5)
        self.peer_3.close()

# ? How to launch:
# poetry run poe test
# --or--
# poetry run python -m unittest discover -s tests -p "tcp_group_chat_simulation_1.py"