# Summary of Changes

### Request Class:

Extended to include metadata for storing the authentication token. The metadata field enables passing the token with every request, ensuring that the server can authenticate and authorize the user.

### Client:

The client now stores the authentication token after a successful login and includes it in the metadata for subsequent requests that require authorization.
The get_user and check_password methods pass the token in metadata to ensure that only authenticated and authorized users can access restricted resources.

### Server:

The server retrieves the token from the metadata of each incoming request and validates it.
Role-based access control is enforced. Only users with the admin role are allowed to access sensitive data, such as user information.

### CLI:

The command-line interface (CLI) allows users to authenticate, pass the token, and make authorized requests based on their role.

# Test

### 1. Test Authentication
Objective: Verify that the client can authenticate successfully and store the token.
Test:

credentials = Credentials(id='user1', password='password123')
assert client.authenticate(credentials) == True  # Should return True
 ### 2. Test Unauthorized Access (No Token)
Objective: Ensure that the client cannot make any authorized requests without an authentication token.
Test:

try:
    response = client.get_user('user1')  # Should raise an error if not authenticated
except RuntimeError as e:
    assert str(e) == "Authentication required"  # Error should indicate authentication is required
### 3. Test Role-Based Authorization (Admin vs User)
Objective: Ensure that only users with the admin role can access restricted resources (e.g., get_user).
Test:

admin_credentials = Credentials(id='admin_user', password='admin_pass')
user_credentials = Credentials(id='user1', password='user_pass')

 """Authenticate as admin and access user data"""
assert client.authenticate(admin_credentials) == True
response = client.get_user('user1')  # Should succeed for admin
assert response['result'] == 'Success'

 """Authenticate as regular user and try to access restricted data"""
assert client.authenticate(user_credentials) == True
try:
    response = client.get_user('user1')  # Should fail for non-admin
except RuntimeError as e:
    assert str(e) == "Unauthorized: Admin role required"  # Unauthorized error for non-admin

### 4. Test Token Expiration
Objective: If implement token expiration, verify that the server rejects expired tokens.
Test:

expired_token_credentials = Credentials(id='user1', password='password123')
assert client.authenticate(expired_token_credentials) == True
 """Simulate token expiration and try to access data"""
try:
    response = client.get_user('user1')  # Should fail if token is expired
except RuntimeError as e:
    assert str(e) == "Invalid or expired token"  # Should show token expiration error

### 5. Test Successful Requests
Objective: Verify that valid requests (with a valid token) are processed successfully.
Test:

credentials = Credentials(id='user1', password='password123')
assert client.authenticate(credentials) == True
response = client.get_user('user1')  # Should succeed with valid token
assert response['result'] == 'Success'