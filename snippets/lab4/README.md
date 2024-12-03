### Updates to the `Request` Class and Authentication Workflow  

The `Request` class now includes a new field, `metadata`. This field is a dictionary that can optionally be set to `None` if no additional data is required.  

#### Server Authentication Behavior  
The server has been enhanced to validate user authentication before handling the `get_user` procedure. The following rules apply:  

- If an authentication token is missing, the server will return the error: **"Missing metadata(token). You must be authenticated to use this method."**  
- If an invalid token is provided, the server will respond with: **"You are not authenticated"**  
- If the user does not have admin privileges, the server will reject the request with: **"You don't have admin role"**  

#### Client Behavior  
The client is responsible for storing the authentication token received during the authentication process. This token must be included in all subsequent `get_user` requests sent to the server.  

Testing

Open first terminal and lanch:  
python -m snippets -l 4 -e 2 8080

Open second terminal fill in the areas marked with uppercase  with appropriate information of your choice and lanch:  
python -m snippets -l 4 -e 4 127.0.0.1:8080 get -u "USERNAME" --path TOKENNAME    *TOKENNAME is the name of file which stores json format token. Usually is same as USERNAME*  
python -m snippets -l 4 -e 4 127.0.0.1:8080 add -u "USERNAME" -a "EMAIL" -n "NAME" -r user -p "PASSWORD" -r admin  
python -m snippets -l 4 -e 4 127.0.0.1:8080 authenticate -u "USERNAME" -p "PASSWORD" --path TOKENNAME  
python -m snippets -l 4 -e 3 127.0.0.1:8080
