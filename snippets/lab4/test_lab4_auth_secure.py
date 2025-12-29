import sys
from snippets.lab4.example3_rpc_client import RemoteUserDatabase, RemoteAuthenticationService
from snippets.lab4.example1_presentation import serialize, deserialize
from snippets.lab4.users import User, Credentials, Role
from snippets.lab3 import address


def print_step(msg):
	print("\n=== " + msg + " ===")


def expect_error(fn, expected):
	try:
		fn()
	except Exception as e:
		msg = " ".join(e.args)
		print("Got error:", msg)
		assert expected in msg, f"Expected '{expected}', got '{msg}'"
		return
	raise AssertionError(f"Expected error '{expected}' but no error occurred")


def main():
	if len(sys.argv) != 2:
		print("Usage: python -m snippets.lab4.test_lab4_auth_secure ip:port")
		sys.exit(1)

	server_addr = address(sys.argv[1])

	# Create client stubs
	user_db = RemoteUserDatabase(server_addr)
	auth = RemoteAuthenticationService(server_addr)

	# Link per propagazione token
	auth._linked_user_db = user_db

	# Create admin
	print_step("ADD ADMIN USER")
	admin = User(
		username="admin",
		emails=["admin@mail.com"],
		full_name="Admin User",
		role=Role.ADMIN,
		password="secret",
	)
	user_db.add_user(admin)

	# Get without token -> FAIL
	print_step("GET WITHOUT TOKEN SHOULD FAIL")
	expect_error(lambda: user_db.get_user("admin"), "Missing token")

	# Admin login
	print_step("ADMIN LOGIN")
	admin_token = auth.authenticate(Credentials("admin", "secret"))
	print("Admin token =", admin_token)

	# Get with valid admin token -> OK
	print_step("GET WITH VALID ADMIN TOKEN")
	res = user_db.get_user("admin")
	print("Result:", res)
	assert res.username == "admin"

	# Create normal user
	print_step("ADD NORMAL USER")
	bob = User(
		username="bob",
		emails=["bob@mail.com"],
		full_name="Bob Builder",
		role=Role.USER,
		password="pass",
	)
	user_db.add_user(bob)

	# Normal user login
	print_step("LOGIN NORMAL USER")
	bob_token = auth.authenticate(Credentials("bob", "pass"))
	print("Bob token =", bob_token)

	# Normal user tries to get admin data -> FAIL
	print_step("NORMAL USER SHOULD NOT BE ABLE TO GET USER DATA")
	expect_error(lambda: user_db.get_user("admin"), "Permission denied")

	# Validate admin token
	print_step("VALIDATE ADMIN TOKEN")
	assert auth.validate_token(admin_token) is True
	print("Admin token is valid")

	# Validate corrupted token
	print_step("VALIDATE CORRUPTED TOKEN")
	bad = admin_token.copy(signature="wrong")
	assert auth.validate_token(bad) is False
	print("Corrupted token is invalid")

	print("\n=== ALL TESTS PASSED ===")


if __name__ == "__main__":
	main()
