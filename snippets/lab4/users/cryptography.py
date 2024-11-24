from ..users import Signer
import hashlib


def compute_sha256_hash(input: str) -> str:
    sha256_hash = hashlib.sha256()
    sha256_hash.update(input.encode('utf-8'))
    return sha256_hash.hexdigest()


class DefaultSigner(Signer):

    def __init__(self, secret: str | None = None):
        if not secret:
            import uuid
            secret = str(uuid.uuid4())
        self.__secret = secret
        super().__init__()

    def sign(self, *args) -> str:
        """
        Defines the default signing algorithm, e.g. sha256(f'{user}{expiration}{secret}')
        """
        return compute_sha256_hash("".join([str(arg) for arg in args]) + self.secret)
    
    @property
    def secret(self) -> str:
        return self.__secret