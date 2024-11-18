from snippets.lab3.exercise_tcp_group_chat import TCPPeer
from snippets.lab3 import clear_log_file
import time

# ! TODO: fix simulation (i.e. output log)
# ! TODO: create desired simulation output file
# ! TODO: Important make nicknames unique!!
# ! TODO: Important to set client port to be deterministic! (otherwise we cannot test it properly)
# ! Problem:    P0 --- P1 --- P2
# !             if P1 disconnects, P0 and P2 cannot communicate!

clear_log_file('./snippets/lab3/chat_log.log')

username_peer_0 = 'User0'
username_peer_1 = 'User1'
username_peer_2 = 'User2'
username_peer_3 = 'User3'

"""
peer_0 = TCPPeer(username=username_peer_0, port=8080, remote_endpoints=None)
peer_1 = TCPPeer(username=username_peer_1, port=8081, remote_endpoints=['localhost:8080'])
peer_2 = TCPPeer(username=username_peer_2, port=8082, remote_endpoints=['localhost:8080','localhost:8081'])
peer_3 = TCPPeer(username=username_peer_3, port=8083, remote_endpoints=['localhost:8080','localhost:8081','localhost:8082'])
"""

peer_0 = TCPPeer(port=8080, remote_endpoints=None)
peer_1 = TCPPeer(port=8081, remote_endpoints=['localhost:8080'])
peer_2 = TCPPeer(port=8082, remote_endpoints=['localhost:8080','localhost:8081'])
peer_3 = TCPPeer(port=8083, remote_endpoints=['localhost:8080','localhost:8081','localhost:8082'])

peer_0.send_message("Hello!", username_peer_0)
time.sleep(3)
peer_1.send_message("Hey!", username_peer_1)
time.sleep(3)
peer_2.send_message("Howdy!", username_peer_2)
time.sleep(3)
peer_3.send_message("Ciao!", username_peer_3)
time.sleep(3)

# ! TODO: fix error (x not in list)
peer_0.close()
time.sleep(3)
peer_1.close()
time.sleep(3)
peer_2.close()
time.sleep(3)
peer_3.close()
time.sleep(3)