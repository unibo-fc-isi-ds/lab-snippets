from snippets.lab3 import Server
from snippets.lab4.users import Token, Role
from snippets.lab4.users.impl import InMemoryUserDatabase, InMemoryAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize, Request, Response
import traceback


class ServerStub(Server):
	def __init__(self, port):
		super().__init__(port, self.__on_connection_event)
		self.__user_db = InMemoryUserDatabase()
		self.__auth = InMemoryAuthenticationService(self.__user_db)

	def __on_connection_event(self, event, connection, address, error):
		match event:
			case 'listen':
				print('Server listening on %s:%d' % address)
			case 'connect':
				connection.callback = self.__on_message_event
			case 'error':
				traceback.print_exception(error)
			case 'stop':
				print('Server stopped')

	def __on_message_event(self, event, payload, connection, error):
		match event:
			case 'message':
				print('[%s:%d] Open connection' % connection.remote_address)
				request = deserialize(payload)
				assert isinstance(request, Request)
				print('[%s:%d] Unmarshall request:' % connection.remote_address, request)
				response = self.__handle_request(request)
				connection.send(serialize(response))
				print('[%s:%d] Marshall response:' % connection.remote_address, response)
				connection.close()
			case 'error':
				traceback.print_exception(error)
			case 'close':
				print('[%s:%d] Close connection' % connection.remote_address)

	def __require_admin(self, request: Request):
		token = request.metadata
		if token is None:
			raise PermissionError("Missing token")
		if not isinstance(token, Token):
			raise PermissionError("Invalid token format")
		if not self.__auth.validate_token(token):
			raise PermissionError("Invalid token")
		if token.user.role is not Role.ADMIN:
			raise PermissionError("Permission denied")

	def __handle_request(self, request):
		try:
			# service: UserDatabase
			if hasattr(self.__user_db, request.name):
				# authorization for read operations
				if request.name == 'get_user':
					self.__require_admin(request)

				method = getattr(self.__user_db, request.name)
				result = method(*request.args)
				return Response(result, None)

			# service: AuthenticationService
			if hasattr(self.__auth, request.name):
				method = getattr(self.__auth, request.name)
				result = method(*request.args)
				return Response(result, None)

			# unknown method
			return Response(None, f"Unknown method {request.name}")

		except Exception as e:
			return Response(None, " ".join(e.args))


if __name__ == '__main__':
	import sys
	server = ServerStub(int(sys.argv[1]))
	while True:
		try:
			input('Close server with Ctrl+D (Unix) or Ctrl+Z (Win)\n')
		except (EOFError, KeyboardInterrupt):
			break
	server.close()
