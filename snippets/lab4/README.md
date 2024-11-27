# RPC Authentication Service - Designed by Jing Yang

## Overview
This project implements an RPC-based authentication service using a client-server architecture. The primary focus is the `authenticate` functionality, allowing clients to exchange credentials for a time-limited token. This token can then be used to validate access to specific services.

## Features
### Authentication Solution
1. **Credential Verification**: Clients provide credentials (username and password), which the server verifies against the user database. The verification process uses the `check_password` method, which compares the SHA-256 hash of the provided password with the stored hash. This ensures that passwords are never stored in plain text, enhancing security.

   - **Code Example**: In the server code, `InMemoryUserDatabase` is used to manage user credentials. The `_compute_sha256_hash` function is called to securely hash passwords before comparison or storage.

2. **Token Generation**: Upon successful verification of credentials, the server generates a token using the `authenticate` method. The token contains information about the user, including the username and expiration timestamp, along with a cryptographic signature that is generated using a secret key held by the server.

   - **Code Example**: The `Token` dataclass is used to structure the generated token, which includes `user`, `expiration`, and `signature` fields. The signature is created by hashing a combination of the user's details, expiration time, and a secret key.

3. **Token Expiration**: Tokens are issued with an expiration time, which is calculated by adding the desired duration to the current timestamp. This ensures that tokens are valid only for a limited period, mitigating risks associated with token misuse.

   - **Code Example**: In the `authenticate` method, the expiration is set using `datetime.now() + timedelta(seconds=duration)` to specify how long the token will be valid.

4. **Signature for Security**: The server signs each token using a secret key, ensuring that clients cannot tamper with the token. The signature is verified when the client attempts to validate the token.

   - **Code Example**: The `_compute_sha256_hash` function is used to create a unique signature for the token by hashing a combination of the user's data, the expiration time, and a server-side secret.

5. **Threaded Client Handling**: Each client connection is managed in its own thread, allowing the server to handle multiple authentication requests concurrently. This is implemented using the `Connection` class, where each connection runs on a separate thread.

   - **Code Example**: The `ServerStub` class uses threading to manage incoming client connections, allowing for multiple clients to be authenticated simultaneously.

### Server-Side Design
1. **User Management**: The server maintains a user database (`InMemoryUserDatabase`), which allows new users to be added and queried. The `add_user` method ensures that usernames and email addresses are unique and securely stores hashed passwords.
2. **Authentication Endpoint**: The `authenticate` endpoint handles client requests by validating credentials and generating tokens. The method returns a `Token` object or an error if the credentials are incorrect.
3. **Token Validation**: The server also provides a `validate_token` method to check the validity of a token. It verifies both the expiration and the cryptographic signature to ensure that the token is authentic and has not expired.

### Client-Side Design
1. **RPC Calls for Authentication**: The client communicates with the server using RPC calls to request authentication. The `RemoteAuthenticationService` class encapsulates these RPC calls, allowing the client to send credentials and receive a token if authentication is successful.
   - **Code Example**: The `rpc` method in `ClientStub` serializes the `Request` object, sends it to the server, and deserializes the `Response` object to receive the token.

2. **Simultaneous Operations**: The client is threaded, allowing it to send and receive messages concurrently. This ensures that the user can keep interacting with the client while waiting for a response from the server.

   - **Code Example**: The client uses a `threading.Thread` to manage sending and receiving messages without blocking user actions.

## How to Test Authentication
### Manual Test
1. **Start the Server**:
   ```bash
   python -m snippets -l 4 -e 2 8083
   ```
2. **Start a Client and create a user**:
   ```bash
   python -m snippets -l 4 -e 4 LOCALHOST:8083 add -u jing -a jing.yang5@studio.unibo.it -n "Jing Yang" -r admin -p "yyyyyjjjjj"  
   ```
3. **Start Authenticate**:
    ```bash
    python -m snippets -l 4 -e 4 LOCALHOST:8083 authenticate -u jing -p "yyyyyjjjjj" -d 3600      
    ```
4. **Validate token**:
    ```bash
    python -m snippets -l 4 -e 4 LOCALHOST:8083 validate -t '<token_string>'
    ```
                                                                 
