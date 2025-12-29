from snippets.lab3 import Client, address
from snippets.lab4.users import User, Credentials, Token, UserDatabase
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response


class ClientStub:
	def __init__(self, server_address: tuple[str, int]):
		self.__server_address = address(*server_address)
		self.__token: Token | None = None

	def rpc(self, name, *args):
		client = Client(self.__server_address)
		try:
			print('# Connected to %s:%d' % client.remote_address)

			# RPC request with metadata (token)
			request = Request(name=name, args=args, metadata=self.__token)
			print('# Marshalling', request, 'towards', "%s:%d" % client.remote_address)

			wire = serialize(request)
			print('# Sending message:', wire.replace('\n', '\n# '))
			client.send(wire)

			response_wire = client.receive()
			print('# Received message:', response_wire.replace('\n', '\n# '))
			response = deserialize(response_wire)

			assert isinstance(response, Response)
			print('# Unmarshalled', response, 'from', "%s:%d" % client.remote_address)

			if response.error:
				raise RuntimeError(response.error)

			return response.result

		finally:
			client.close()
			print('# Disconnected from %s:%d' % client.remote_address)

	def _set_token(self, token: Token | None):
		self.__token = token


class RemoteUserDatabase(ClientStub, UserDatabase):
	def __init__(self, server_address):
		super().__init__(server_address)

	def add_user(self, user: User):
		return self.rpc('add_user', user)

	def get_user(self, id: str) -> User:
		return self.rpc('get_user', id)

	def check_password(self, credentials: Credentials) -> bool:
		return self.rpc('check_password', credentials)


class RemoteAuthenticationService(ClientStub):
	def __init__(self, server_address):
		super().__init__(server_address)
		self._linked_user_db: RemoteUserDatabase | None = None

	def authenticate(self, credentials: Credentials) -> Token:
		token = self.rpc('authenticate', credentials)

		# memorizes token inside this stub
		self._set_token(token)

		# propagates token to linked user_db (session sharing)
		if self._linked_user_db is not None:
			self._linked_user_db._set_token(token)

		return token

	def validate_token(self, token: Token) -> bool:
		return self.rpc('validate_token', token)


if __name__ == '__main__':
	from snippets.lab4.example0_users import gc_user, gc_credentials_ok, gc_credentials_wrong
	import sys

	user_db = RemoteUserDatabase(address(sys.argv[1]))
	auth = RemoteAuthenticationService(address(sys.argv[1]))

	# Link stubs → enables token sharing
	auth._linked_user_db = user_db

	# add admin user
	user_db.add_user(gc_user)

	# unauthorized get_user (must fail)
	try:
		user_db.get_user('gciatto')
	except RuntimeError as e:
		assert 'Missing token' in str(e) or 'Permission denied' in str(e)

	# login as admin → sets token in both stubs
	token = auth.authenticate(gc_credentials_ok[0])

	# now authorized
	assert user_db.get_user('gciatto') == gc_user.copy(password=None)

	# check_password works as before
	for gc_cred in gc_credentials_ok:
		assert user_db.check_password(gc_cred) is True

	assert user_db.check_password(gc_credentials_wrong) is False

	# validate tokens
	assert auth.validate_token(token) is True
	token_bad = token.copy(signature="wrong")
	assert auth.validate_token(token_bad) is False
