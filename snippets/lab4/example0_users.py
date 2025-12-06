from .users import User, Credentials, Role
from .users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from datetime import timedelta, datetime
import time

# ===============================
# Данные для тестов (доступны при импорте)
# ===============================

gc_user = User(
    username='adilet',
    emails={'zhumabay.adilet@unibo.it', 'zhumabay.adilet@gmail.com'},
    full_name='Zhumabay Adilet',
    role=Role.ADMIN,
    password='my secret password',
)

gc_user_hidden_password = gc_user.copy(password=None)

gc_credentials_ok = [
    Credentials(id, gc_user.password) for id in gc_user.ids
]

gc_credentials_wrong = Credentials(
    id='zhumabay.adilet@unibo.it',
    password='wrong password',
)

# ===============================
# Тесты (только при запуске напрямую)
# ===============================
if __name__ == '__main__':
    _PRINT_LOGS = True
    user_db = InMemoryUserDatabase(debug=_PRINT_LOGS)
    auth_service = InMemoryAuthenticationService(user_db, debug=_PRINT_LOGS)

    # Получение несуществующего пользователя → KeyError
    try:
        user_db.get_user('adilet')
    except KeyError as e:
        assert 'User with ID adilet not found' in str(e)

    # Добавление нового пользователя
    user_db.add_user(gc_user)

    # Попытка добавить существующего → ValueError
    try:
        user_db.add_user(gc_user)
    except ValueError as e:
        assert str(e).startswith('User with ID')
        assert str(e).endswith('already exists')

    # Получение существующего пользователя
    assert user_db.get_user('adilet') == gc_user.copy(password=None)

    # Проверка правильных и неправильных credentials
    for gc_cred in gc_credentials_ok:
        assert user_db.check_password(gc_cred) == True
    assert user_db.check_password(gc_credentials_wrong) == False

    # Аутентификация
    try:
        auth_service.authenticate(gc_credentials_wrong)
    except ValueError as e:
        assert 'Invalid credentials' in str(e)

    gc_token = auth_service.authenticate(gc_credentials_ok[0])
    assert gc_token.user == gc_user_hidden_password
    assert gc_token.expiration > datetime.now()
    assert auth_service.validate_token(gc_token) == True

    # Токен с неправильной подписью
    gc_token_wrong_signature = gc_token.copy(signature='wrong signature')
    assert auth_service.validate_token(gc_token_wrong_signature) == False

    # Истёкший токен
    gc_token_expired = auth_service.authenticate(gc_credentials_ok[0], timedelta(milliseconds=10))
    time.sleep(0.1)
    assert auth_service.validate_token(gc_token_expired) == False

    print("All tests passed successfully!")
