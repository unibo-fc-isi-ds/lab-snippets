from snippets.lab3.exercise_tcp_group_chat import TCPPeer
from snippets.lab3 import clear_log_file

# ! TODO: better log file format
# ! TODO: fix simulation (i.e. output log)
# ! TODO: create desired simulation output file

clear_log_file('./snippets/lab3/chat_log.log')

username_peer_0 = 'User0'
username_peer_1 = 'User1'
username_peer_2 = 'User2'

peer_0 = TCPPeer(port=8080, remote_endpoints=None)
peer_1 = TCPPeer(port=8081, remote_endpoints=['localhost:8080'])
peer_2 = TCPPeer(port=8082, remote_endpoints=['localhost:8080','localhost:8081'])

peer_0.send_message("Hello!", username_peer_0)
peer_1.send_message("Hey!", username_peer_1)
peer_2.send_message("Howdy!", username_peer_2)

peer_0.close()
peer_1.close()
peer_2.close()