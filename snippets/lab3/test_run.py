import subprocess
import threading
import time
import sys

SERVER_HOST = '127.0.0.1'
SERVER_PORT = 8081

def start_server():
    print("Starting server...")
    server_cmd = [
        "poetry", "run", "python", "-m", "snippets.lab3.exercise_tcp_group_chat", 
        "server", str(SERVER_PORT)
    ]
    return subprocess.Popen(server_cmd)

def start_client(username, server_address, peer_endpoints=None):
    print(f"Starting client {username}...")
    client_cmd = [
        "poetry", "run", "python", "-m", "snippets.lab3.exercise_tcp_group_chat", 
        "client", f"{server_address[0]}:{server_address[1]}"
    ]
    if peer_endpoints:
        peer_args = ",".join(f"{peer[0]}:{peer[1]}" for peer in peer_endpoints)
        client_cmd.append(peer_args)
    return subprocess.Popen(client_cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def client_behavior(client_proc, username, messages, disconnect_after=None):
    try:
        client_proc.stdin.write(f"{username}\n")
        client_proc.stdin.flush()
        
        for i, msg in enumerate(messages):
            client_proc.stdin.write(f"{msg}\n")
            client_proc.stdin.flush()
            print(f"{username} sent: {msg}")
            time.sleep(2)
            
            if disconnect_after and i == disconnect_after - 1:
                print(f"{username} disconnects unexpectedly.")
                client_proc.terminate()
                return

        client_proc.stdin.close()
        
    except Exception as e:
        print(f"Error in client {username}: {e}")

def main():
    server = start_server()
    time.sleep(1)
    
    server_address = (SERVER_HOST, SERVER_PORT)
    client_endpoints = [
        (SERVER_HOST, SERVER_PORT),
    ]

    client1 = start_client("jingyang", server_address, client_endpoints)
    client2 = start_client("mobius", server_address, client_endpoints)
    client3 = start_client("YJ", server_address, client_endpoints)
    
    threading.Thread(target=client_behavior, args=(client1, "jingyang", [
        "Hello everyone!", "This is jingyang.", "How's everyone doing?", "What are you up to?", "Goodbye all!"
    ], None)).start()

    threading.Thread(target=client_behavior, args=(client2, "mobius", [
        "Hey jingyang!", "Nice to meet you all.", "I am doing great, thanks for asking.", "How about you?", "See you soon!"
    ], 3)).start() 

    threading.Thread(target=client_behavior, args=(client3, "YJ", [
        "Hi there!", "This is YJ joining the chat.", "Nice to see everyone here.", "Hope you all have a great day!", "Signing off!"
    ], None)).start()

    time.sleep(20)

    client1.terminate()
    client2.terminate()
    client3.terminate()
    server.terminate()
    print("Test completed.")

if __name__ == "__main__":
    main()
