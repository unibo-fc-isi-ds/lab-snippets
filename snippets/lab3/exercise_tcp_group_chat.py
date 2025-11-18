from snippets.lab2 import *
import threading
import sys

##Non devo più distinguere tra client e server, ma solo tra peer

class Peer(Connection):   
    def __init__(self, port, peers=None):
        super().__init__(port, peers)
        