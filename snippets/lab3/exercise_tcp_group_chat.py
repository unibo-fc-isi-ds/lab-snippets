from snippets.lab3 import *
import sys
import threading


peers = {}  # 存储所有连接的对等体 {address: connection}


def on_message_received(event, payload, connection, error):
    match event:
        case 'message':
            print(f"Message from {connection.remote_address}: {payload}")
            broadcast_message(payload, connection.remote_address)
        case 'close':
            print(f"Connection with {connection.remote_address} closed")
            del peers[connection.remote_address]
        case 'error':
            print(error)


def broadcast_message(message, sender_address=None):
    """将消息广播给所有已知的对等体"""
    for addr, conn in peers.items():
        if addr != sender_address:  # 避免将消息发送回发送者
            conn.send(message)


def start_server(port):
    def on_new_connection(event, connection, address, error):
        match event:
            case 'listen':
                print(f"Server listening on port {port} at {', '.join(local_ips())}")
            case 'connect':
                print(f"Connected by: {address}")
                connection.callback = on_message_received
                peers[address] = connection
            case 'stop':
                print("Stopped listening")
            case 'error':
                print(error)

    server = Server(port, on_new_connection)
    return server


def connect_to_peer(remote_endpoint):
    """连接到另一个对等体"""
    try:
        client = Client(address(remote_endpoint), on_message_received)
        print(f"Connected to {client.remote_address}")
        peers[client.remote_address] = client
    except Exception as e:
        print(f"Failed to connect to {remote_endpoint}: {e}")


if __name__ == "__main__":
    port = int(sys.argv[1])
    remote_peers = sys.argv[2:]  # 其他对等体的地址列表

    # 启动服务器以监听传入连接
    server = start_server(port)

    # 尝试连接到其他对等体
    for peer_addr in remote_peers:
        connect_to_peer(peer_addr)

    username = input('Enter your username to start the chat:\n')
    print('Type your message and press Enter to send it. Messages from other peers will be displayed below.')
    
    try:
        while True:
            content = input()
            if content.lower() == "exit":
                break
            broadcast_message(message(content, username))
    except (EOFError, KeyboardInterrupt):
        print("\nExiting chat...")
    
    # 关闭所有连接
    for conn in peers.values():
        conn.close()
    server.close()
