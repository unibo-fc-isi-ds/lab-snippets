from .example3_rpc_client import *
import argparse
import sys


if __name__ == '__main__':

	parser = argparse.ArgumentParser(
		prog=f'python -m snippets -l 4 -e 4',
		description='RPC client for user database and authentication service',
		exit_on_error=False,
	)

	parser.add_argument('address', help='Server address in the form ip:port')
	parser.add_argument(
		'command',
		help='Method to call',
		choices=['add', 'get', 'check', 'login', 'validate']
	)

	parser.add_argument('--user', '-u', help='Username')
	parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
	parser.add_argument('--name', '-n', help='Full name')
	parser.add_argument(
		'--role',
		'-r',
		help='Role (defaults to "user")',
		choices=['admin', 'user'],
		default='user',
	)
	parser.add_argument('--password', '-p', help='Password')
	parser.add_argument('--token', '-t', help='Serialized token (JSON string)')
	parser.add_argument('--token-file', help='Read token from file')
	parser.add_argument('--save-token', help='Write token JSON to file')

	if len(sys.argv) > 1:
		args = parser.parse_args()
	else:
		parser.print_help()
		sys.exit(0)

	args.address = address(args.address)
	user_db = RemoteUserDatabase(args.address)
	auth = RemoteAuthenticationService(args.address)

	# optional: preload token into client stubs, so that RPC calls include metadata
	preloaded_token = None
	if args.token_file:
		with open(args.token_file) as f:
			token_data = f.read()
		preloaded_token = deserialize(token_data)
	elif args.token:
		preloaded_token = deserialize(args.token)

	if preloaded_token is not None:
		if not isinstance(preloaded_token, Token):
			raise ValueError("Invalid token format")
		# set token into both client stubs, so subsequent RPC calls carry metadata
		user_db._ClientStub__token = preloaded_token
		auth._ClientStub__token = preloaded_token

	try:
		ids = (args.email or []) + [args.user]
		ids = [x for x in ids if x]

		match args.command:
			case 'add':
				if not args.password:
					raise ValueError("Password is required")
				if not args.name:
					raise ValueError("Full name is required")
				if not args.user:
					raise ValueError("Username is required")
				user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
				print(user_db.add_user(user))

			case 'get':
				if not ids:
					raise ValueError("Username or email address is required")
				print(user_db.get_user(ids[0]))

			case 'check':
				if not ids:
					raise ValueError("Username or email address is required")
				if not args.password:
					raise ValueError("Password is required")
				credentials = Credentials(ids[0], args.password)
				print(user_db.check_password(credentials))

			case 'login':
				if not ids:
					raise ValueError("Username or email address is required")
				if not args.password:
					raise ValueError("Password is required")
				credentials = Credentials(ids[0], args.password)
				token = auth.authenticate(credentials)
				print(token)

				if args.save_token:
					with open(args.save_token, 'w') as f:
						f.write(serialize(token))

			case 'validate':
				# qui usiamo esplicitamente il token passato o caricato,
				# indipendentemente dal pre-caricamento negli stub
				if args.token_file:
					with open(args.token_file) as f:
						token_data = f.read()
					token = deserialize(token_data)
				elif args.token:
					token = deserialize(args.token)
				elif preloaded_token is not None:
					token = preloaded_token
				else:
					raise ValueError("Token or --token-file is required")

				if not isinstance(token, Token):
					raise ValueError("Invalid token format")

				print(auth.validate_token(token))

			case _:
				raise ValueError(f"Invalid command '{args.command}'")

	except RuntimeError as e:
		print(f'[{type(e).__name__}]', *e.args)
	except ValueError as e:
		print(f'[ValueError]', *e.args)
