from .example3_rpc_client import *
from .example1_presentation import Serializer
import argparse
import ast
from datetime import datetime
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
                print(user_db.add_user(user, None))
            case 'get': # E' un operazione che richiede autenticazione
                if args.role == Role.ADMIN :
                    
                    if not args.tokensig :
                        raise ValueError("Token is required")
                    else :
                        print(user_db.get_user(ids[0]), args.tokensig)

                else :
                    raise ValueError("Reading user data is available only for ADMIN user")
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

                authentication_token = Serializer.serialize(token) #serializzo l'oggetto token in una stringa JSON

                print('Autentication successful :', authentication_token)

            case 'validate': # E' un operazione che richiede autenticazione
                if not args.tokensig:
                    raise ValueError("Token signature is required")
                
                if not args.tokenexp:
                    raise ValueError("Token expiration is required")
                
                utente = User(username=args.user, emails=list(args.email or []), full_name=args.name, role=args.role, password=args.password)
                
                #Converto la stringa in datetime
                te_tuple = ast.literal_eval(args.tokenexp)
                te_datetime = datetime(*te_tuple)

                token = Token(utente, expiration=te_datetime, signature=args.tokensig)
                
                if auth_service.validate_token(token):
                    print('Token is valid')
                else:
                    print('Token is invalid or expired')
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
