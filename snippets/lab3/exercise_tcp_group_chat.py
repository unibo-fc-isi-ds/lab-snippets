class Message():
    # Distinguere messaggi interni da messaggi esterni
    pass

class Peer():
    def send(self, message: Message):
        pass
    def receive(self) -> Message:
        pass
    def connect(self, peers: list['Peer']):
        pass
    def disconnect(self, peers: list['Peer']):
        pass
    # funzione privata periodica di controllo della rete

class Controller():
    def handleOutputMessage(self, message: Message):
        pass
    def handleInputMessage(self, message: Message):
        pass

class View():
    def outputMessage(self, message: Message):
        pass
    def inputMessage(self) -> Message:
        pass