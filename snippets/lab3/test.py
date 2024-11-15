import subprocess
import threading
import time
import random

HOST = 'localhost'
PORT = 8080
PEER_NUM = 4
RANDOM_PHRASES = [
    "I love sunny days.",
    "Where is my coffee?",
    "Let's meet tomorrow.",
    "I enjoy playing the guitar.",
    "How are you feeling today?",
    "It's a beautiful morning.",
    "Time flies when you're having fun.",
    "I need some fresh air.",
    "She is always so positive.",
    "I can't wait for the weekend.",
    "Do you like coffee or tea?",
    "The sky is so clear today.",
    "I have a new book to read.",
    "Let's go for a walk.",
    "What's the plan for tonight?",
    "This place feels like home.",
    "I love rainy days too.",
    "What time is the meeting?",
    "I hope you have a great day.",
    "I'm feeling pretty good today."
]

def create_peer(num):
    print(f"[TEST] Starting peer number {num}")
    cmd = [
        "poetry", "run", "python", "-m", 
        "snippets.lab3.exercise_tcp_group_chat", 
        str(PORT + num)
    ]
    cmd.extend([f"localhost:{PORT + num - i}" for i in range(1, num + 1)])
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

def client_behavior(client_proc, num, messages, disconnect_after=None):
    try:
        client_proc.stdin.write(f"{num}\n")
        client_proc.stdin.flush()
        
        for i, msg in enumerate(messages):
            client_proc.stdin.write(f"{msg}\n")
            client_proc.stdin.flush()
            print(f"{num}: {msg}")
            time.sleep(2)
            
            if disconnect_after and i == disconnect_after - 1:
                print(f"[TEST] {num} disconnects")
                client_proc.terminate()
                return

        client_proc.stdin.close()
        
    except Exception as e:
        print(f"[TEST] Error in client {num}: {e}")

def main():
    peers = []
    threads = []

    # Creates each peer
    for i in range(PEER_NUM):
        peers.append(create_peer(i))
    
    for i in range(PEER_NUM):
        thread = threading.Thread(
            target=client_behavior, 
            args=(peers[i], i, random.sample(RANDOM_PHRASES, 5), random.randint(1, 5))  # The exit of each peer is choosen randomly
        )
        threads.append(thread)
        thread.start()
    
    # Wait the end of every thread
    for thread in threads:
        thread.join()

    for peer in peers:
        peer.terminate()
    
    time.sleep(2)
    print("[TEST] Test completed.")

if __name__ == "__main__":
    main()