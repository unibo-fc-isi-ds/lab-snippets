from snippets.lab4.example1_presentation import deserialize, serialize
from .users import Token
import os
from pathlib import Path

TOKENS_DIRECTORY = 'Tokens'

class TokenHandler:
    def __init__(self, directory: str = TOKENS_DIRECTORY):
        self.__dir = Path(directory)
        self.__dir.mkdir(parents=True, exist_ok=True)

    def save_token(self, token: Token):
        try:
            file_path = self.__dir / f"{token.user.username}.json"
            with file_path.open('w') as file:
                serialized = serialize(token)
                file.write(serialized)
        except Exception as e:
            raise RuntimeError(f"Failed to save token for {token.user.username}: {e}")

    def load_token(self, username: str) -> Token:
        try:
            file_path = self.__dir / f"{username}.json"
            with file_path.open('r') as file:
                return deserialize(file.read())
        except FileNotFoundError:
            raise FileNotFoundError(f"No token found for user '{username}'")
        except Exception as e:
            raise RuntimeError(f"Failed to load token for {username}: {e}")

