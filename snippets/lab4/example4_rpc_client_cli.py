from .example3_rpc_client import *
import argparse
import sys


if __name__ == '__main__':

    # Parsing dei parametri della riga di comando
    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    #Argomenti posizionali : obbligatori
    parser.add_argument('address', help='Server address in the form ip:port')
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'check', 'authenticate', 'validate'])
    #Argomenti opzionali : non obbligatori (iniziano sempre con -- o -)
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')
    parser.add_argument('--tokensig', '-ts', help='token signature string')
    parser.add_argument('--tokenexp', '-te', help='Token expiration string')

    if len(sys.argv) > 1: 
        args = parser.parse_args() #args contiene tutti gli argomenti passati da linea di comando
        #per accedere a un certo argomento, uso args.nome_argomento
    else: #se non ho fornito argomenti, stampo l'help e esco
        parser.print_help()
        sys.exit(0)

    tuple_address = address(args.address) # converte la stringa ip:port in una tupla (ip, port)
    user_db = RemoteUserDatabase(tuple_address)
    auth_service = RemoteAuthenticationService(tuple_address)

    try :
        ids = (args.email or []) + [args.user] #creo una lista di id (username + email)
        if len(ids) == 0:
            raise ValueError("Username or email address is required")
        match args.command:
            case 'add':
                if not args.password:
                    raise ValueError("Password is required")
                if not args.name:
                    raise ValueError("Full name is required")
                user = User(args.user, args.email, args.name, Role[args.role.upper()], args.password)
                print(user_db.add_user(user))
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                token = auth_service.authenticate(credentials)
                print('Autentication successful - Token:', token)
            case 'validate': #posso validare un token solo dopo essermi autenticato : lo copio e incollo dall'output del comando precedente
                if not args.tokensig:
                    raise ValueError("Token signature is required")
                
                if not args.tokenexp:
                    raise ValueError("Token expiration is required")
                
                user = User(username=args.user, emails=set(args.email or []), full_name=None, role=Role.USER, password=None)
                token = Token(user=user, expiration=args.tokenexp, signature=args.tokensig)

                if auth_service.validate_token(token):
                    print('Token is valid')
                else:
                    print('Token is invalid or expired')
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
