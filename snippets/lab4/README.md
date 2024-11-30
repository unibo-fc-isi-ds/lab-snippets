## Authentication & validation

Upon authentication, a `<user>.json` file, containing the token's information, including its expiration date in ISO format, is created in the local `./tokens` directory, handled by the `TokenStorage` class.

## Secure access

Upon calling `get`, the user credentials (passed via CLI arguments) are checked:
1. The match is first checked in the user DB;
2. The token is retrieved and validated;
3. The user (retrieved from the token) is checked for an admin role.

If any of these steps fail, an error is raised.

## Usage

Along with the already existing CLI arguments, the following were added:

- `auth -u user -p psw`: authenticates the user and saves its token into the `./tokens` directory;
- `validate -u user -p psw`: validates the saved token for the user;
- `get -u user --auth-user user2 --auth-password psw`: retrieves the data for `user`, ensuring `user2` with password `psw` has the admin role.

Unit tests can be run via: `python -m unittest snippets.lab4.test`.

The system was developed and tested on macOS.