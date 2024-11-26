from .example3_rpc_client import *
from .example1_presentation import Serializer, Deserializer
import argparse
import sys

# per indicare la directory specifica dove verranno salvati (e letti) i tokens creati
TOKEN_DIR = './snippets/lab4/savedTokens'

# creo i metodi di lettura e scrittura su un file dei tokens generati
def save_token(user, token: Token):
    with open(f'{TOKEN_DIR}/{user}.json', 'w') as file_write:
        serialized_token = Serializer().serialize(token) # serializzo qua il token e lo scrivo poi su file
        file_write.write(serialized_token)

def read_token(user) -> Token:
    with open(f'{TOKEN_DIR}/{user}.json', 'r') as read_file:
        return Deserializer().deserialize(read_file.read())
        #return deserializer.deserialize(f.read())

# questa è l'interfaccia command-line creata per l'utente, che si basa su utente per performare invocazioni su Server
# (ovviamente ognuno può fare la propria Interfaccia differente, tipo una GUI)
if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        prog=f'python -m snippets -l 4 -e 4',
        description='RPC client for user database',
        exit_on_error=False,
    )
    parser.add_argument('address', help='Server address in the form ip:port')
    # aggiunti i comandi di autenticazione e di validazione del token
    parser.add_argument('command', help='Method to call', choices=['add', 'get', 'authenticate', 'validate_token', 'check'])
    parser.add_argument('--user', '-u', help='Username')
    parser.add_argument('--email', '--address', '-a', nargs='+', help='Email address')
    parser.add_argument('--name', '-n', help='Full name')
    parser.add_argument('--role', '-r', help='Role (defaults to "user")', choices=['admin', 'user'])
    parser.add_argument('--password', '-p', help='Password')

    if len(sys.argv) > 1:
        args = parser.parse_args()
    else:
        parser.print_help()
        sys.exit(0)

    args.address = address(args.address)
    user_db = RemoteUserDatabase(args.address)
    authentication_service = RemoteAuthenticationService(args.address) # aggiunto il servizio remoto di autenticazione

    try :
        ids = (args.email or []) + [args.user]
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
            # sono aggiunti qua i modi per gestire da comando richieste di autenticazione e validazione del token
            # nel caso di richiesta di autenticazione, devo passare sia l'ID (username), sia la password
            case 'authenticate':
                if not args.password:
                    raise ValueError("Password is required")
                credentials = Credentials(ids[0], args.password)
                # stampo qui il risultato del servizio di autenticazione
                token = authentication_service.authenticate(credentials)
                print("generated token is: ", token)
                save_token(args.user, token)
            # nel caso di validazione del token, leggo prima di tutto dal file il token
            case 'validate_token':
                userToken = read_token(args.user)
                if authentication_service.validate_token(userToken):
                    print("Your token is valid!")
                else:
                    print("Your token has expired! Generate a new one!")
            case 'get':
                print(user_db.get_user(ids[0]))
            case 'check':
                credentials = Credentials(ids[0], args.password)
                print(user_db.check_password(credentials))
            case _:
                raise ValueError(f"Invalid command '{args.command}'")
    except RuntimeError as e:
        print(f'[{type(e).__name__}]', *e.args)
