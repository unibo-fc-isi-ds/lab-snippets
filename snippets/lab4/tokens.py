from snippets.lab4.example1_presentation import deserialize, serialize
from .users import Token
import os

TOKENS_DIR = 'tokens'

class TokenStorage():
    def __init__(self, directory: str = TOKENS_DIR):
        self.__dir = directory
        os.makedirs(directory, exist_ok=True)

    def save(self, token: Token):
        with open(f"{self.__dir}/{token.user.username}.json", 'w') as file:
            serialized = serialize(token)
            file.write(serialized)

    def load(self, username: str) -> Token:
        with open(f"{self.__dir}/{username}.json", 'r') as file:
            return deserialize(file.read())

    def delete(self, id: str):
        os.remove(f"{self.__dir}/{id}.json")

    def __contains__(self, id: str) -> bool:
        return os.path.isfile(f"{self.__dir}/{id}.token")