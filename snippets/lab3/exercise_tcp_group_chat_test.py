from snippets.lab3.exercise_tcp_group_chat import TCPPeer
from snippets.lab3 import clear_log_file
import time
import re

# ? How to launch:
# ? poetry run python -m snippets -l 3 -e sim_1

# ! TODO: create desired simulation output file

# ! Problem:    P0 --- P1 --- P2
# !             if P1 disconnects, P0 and P2 cannot communicate!

def replace_peers(log_file_path):
    peer_map = {}
    peer_counter = 0
    
    def get_or_create_label(peer):
        nonlocal peer_counter
        if peer not in peer_map:
            peer_map[peer] = f"Peer_{peer_counter}"
            peer_counter += 1
        return peer_map[peer]

    with open(log_file_path, 'r') as log_file:
        log_lines = log_file.readlines()
    
    new_log_lines = []
    for line in log_lines:
        peers = re.findall(r"\('.*?', \d+\)", line)
        if len(peers) == 2:
            sender, receiver = peers
            sender_label = get_or_create_label(sender)
            receiver_label = get_or_create_label(receiver)
            new_line = line.replace(sender, sender_label).replace(receiver, receiver_label)
            new_log_lines.append(new_line)
    
    return new_log_lines

def compare_files(file1_path, file2_path):
    with open(file1_path, 'r') as file1, open(file2_path, 'r') as file2:
        file1_lines = file1.readlines()
        file2_lines = file2.readlines()

    file1_lines = sorted([line.strip() for line in file1_lines])
    file2_lines = sorted([line.strip() for line in file2_lines])

    if file1_lines == file2_lines:
        ...

clear_log_file('./snippets/lab3/chat_log.log')

username_peer_0: str = 'User0'
username_peer_1: str = 'User1'
username_peer_2: str = 'User2'
username_peer_3: str = 'User3'

peer_0 = TCPPeer(username=username_peer_0, port=8080, remote_endpoints=None)
peer_1 = TCPPeer(username=username_peer_1, port=8081, remote_endpoints=['localhost:8080'])
peer_2 = TCPPeer(username=username_peer_2, port=8082, remote_endpoints=['localhost:8080','localhost:8081'])
peer_3 = TCPPeer(username=username_peer_3, port=8083, remote_endpoints=['localhost:8080','localhost:8081','localhost:8082'])

peer_0.send_message("Hello!")
time.sleep(3)
peer_1.send_message("Hey!")
time.sleep(3)
peer_2.send_message("Howdy!")
time.sleep(3)
peer_3.send_message("Ciao!")
time.sleep(3)

# ! TODO: output in another file and then assert compare
new_log = replace_peers("./snippets/lab3/chat_log.log") 
for line in new_log: 
    print(line)

time.sleep(5)
peer_0.close()
time.sleep(5)
peer_1.close()
time.sleep(5)
peer_2.close()
time.sleep(5)
peer_3.close()
time.sleep(5)