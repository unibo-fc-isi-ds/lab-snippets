from .example3_rpc_client import *
from .example1_presentation import Serializer
import argparse
import ast
import sys
import os
from datetime import datetime

TOKEN_FILE = 'token.json' #Nome del file dove salvo il token

def save_token(token: Token):
    #Salva il token su file
    with open(TOKEN_FILE, 'w') as f:
        f.write(serialize(token).replace('\n', '').replace('  ', '')) #Lo salvo su un unica riga per essere più facile da incollare da terminale
    print(f'# Token saved to {TOKEN_FILE}')

def load_token() -> Token | None:
    #Carica il token dal file, se esiste
    if not os.path.exists(TOKEN_FILE):
        return None
    try:
        with open(TOKEN_FILE, 'r') as f:
            token = deserialize(f.read())
        print(f'# Token loaded from {TOKEN_FILE}')
        return token
    except Exception as e:
        print(f'# Failed to load token: {e}')
        return None

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
    parser.add_argument('--token', '-t', help='token in JSON string')

    if len(sys.argv) > 1: 
        args = parser.parse_args() #args contiene tutti gli argomenti passati da linea di comando
        #per accedere a un certo argomento, uso args.nome_argomento
    else: #se non ho fornito argomenti, stampo l'help e esco
        parser.print_help()
        sys.exit(0)

    tuple_address = address(args.address) # converte la stringa ip:port in una tupla (ip, port)
    user_db = RemoteUserDatabase(tuple_address)
    auth_service = RemoteAuthenticationService(tuple_address)

    #Carica il token (se esiste)
    saved_token = load_token()
    if saved_token:
        user_db.set_token(saved_token)
        auth_service.set_token(saved_token)

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
            case 'get': # E' un operazione che richiede autenticazione

                # Il token è già memorizzato in user_db dopo authenticate
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
                
                # Autentica e ottieni il token
                token = auth_service.authenticate(credentials)

                #Sincronizza il token con user_db
                user_db.set_token(token)
                
                #Salva il token su file
                save_token(token)
                print(f"# Token saved to {TOKEN_FILE}")
                            
            case 'validate':
                if not args.token:
                    raise ValueError("Token required as a JSON string via CLI")

                token = deserialize(args.token)

                if not isinstance(token, Token):
                    raise ValueError("Token must be a JSON string")

                print(auth_service.validate_token(token))

            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
