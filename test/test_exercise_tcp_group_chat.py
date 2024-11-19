from threading import Thread
from time import sleep, time
import unittest
from unittest.mock import MagicMock, patch
from snippets.lab3.exercise_tcp_group_chat import MultiTCPChatPeer, Peer
import socket

class TestMultiTCPChatPeer(unittest.TestCase):
    TIMEOUT = 5

    def setUp(self):
        self.multiTCPChatPeer = MultiTCPChatPeer(
            port=12345,
            username="test_user",
            remote_endpoints=[],
            on_message=MagicMock(),
            on_peer_connected=MagicMock(),
            on_peer_disconnected=MagicMock(),
            on_name_changed=MagicMock()
        )

    def test_initialization(self):
        self.assertEqual(self.multiTCPChatPeer.username, "test_user")
        self.assertEqual(self.multiTCPChatPeer.listen_port, 12345)
        self.assertFalse(self.multiTCPChatPeer.closed)
        self.assertEqual(len(self.multiTCPChatPeer.remote_peers), 0)

    def test_send_receive_message(self):
        # Try to make 2 peers communicate
        MSG = "Hello"
        peer_connected: bool = False
        def on_peer_connected(peer):
            nonlocal peer_connected
            peer_connected = True
        def on_message(peer, message):
            self.assertEqual(message, MSG)
            self.multiTCPChatPeer.send_message(MSG)

        self.multiTCPChatPeer._on_peer_connected = on_peer_connected
        peer2 = MultiTCPChatPeer(
            port=12346,
            username="peer1",
            remote_endpoints=[("127.0.0.1", 12345)],
            on_message=MagicMock(),
            on_peer_connected=MagicMock(),
            on_peer_disconnected=MagicMock(),
            on_name_changed=MagicMock()
        )
        now = time()
        while not peer_connected and time() - now < self.TIMEOUT:
            sleep(0.1)
        self.assertTrue(peer_connected, "peer_connected not called")
        peer2.send_message(MSG)

    def test_close(self):
        self.multiTCPChatPeer.close()
        self.assertTrue(self.multiTCPChatPeer.closed, "Peer not closed")
        

