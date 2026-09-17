from datetime import datetime, timedelta
import secrets
from typing import Optional
from . import User, Credentials, Token, UserDatabase, AuthenticationService


class InMemoryAuthenticationService(AuthenticationService):
    def __init__(self, user_db: UserDatabase, debug: bool = False):
        self.user_db = user_db
        self.debug = debug

    def authenticate(
        self,
        credentials: Credentials,
        duration: Optional[timedelta] = None
    ) -> Token:
        if not self.user_db.check_password(credentials):
            raise ValueError("Invalid credentials")

        user = self.user_db.get_user(credentials.id)
        # Убираем пароль из токена
        user_hidden = user.copy(password=None)

        if duration is None:
            duration = timedelta(hours=1)

        expiration = datetime.now() + duration
        signature = secrets.token_hex(16)

        token = Token(user=user_hidden, expiration=expiration, signature=signature)

        if self.debug:
            print(f"[Auth] Generated token for {credentials.id}: {token}")

        return token

    def validate_token(self, token: Token) -> bool:
        if token.expiration < datetime.now():
            if self.debug:
                print(f"[Auth] Token expired: {token}")
            return False

        # Простая проверка подписи (в реальном мире нужна HMAC/подпись)
        if not token.signature:
            if self.debug:
                print(f"[Auth] Invalid token signature: {token}")
            return False

        return True
