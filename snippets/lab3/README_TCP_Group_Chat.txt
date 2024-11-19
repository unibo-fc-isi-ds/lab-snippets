
# TCP Group Chat

## Descrizione
Questo progetto implementa una chat di gruppo TCP utilizzando socket e threading in Python. 
L'applicazione consente comunicazione in tempo reale tra i client tramite un server centrale.

## Funzionalità
- Supporto per connessioni multiple.
- Invio e ricezione di messaggi in tempo reale.
- Comando `{exit}` per disconnettersi dalla chat.
- Compatibilità con Unix, macOS e Windows.

## Motivazione delle Scelte
- **Socket e Threading:** Consentono una gestione efficiente delle connessioni multiple e la comunicazione in tempo reale.
- **Cross-Platform Compatibility:** La soluzione è progettata per funzionare su diversi sistemi operativi.

## Struttura del Progetto
- **Server:** Gestisce le connessioni dei client e distribuisce i messaggi a tutti i client connessi.
- **Client:** Consente agli utenti di inviare messaggi e riceverli in tempo reale.

## Come Testare
### Avvia il Server
1. Esegui il seguente comando:
   ```bash
   python exercise_tcp_group_chat.py server <HOST> <PORT>
   ```
   Sostituisci `<HOST>` con l'indirizzo IP del server e `<PORT>` con il numero di porta.

### Avvia il Client
1. Esegui il seguente comando:
   ```bash
   python exercise_tcp_group_chat.py client <HOST> <PORT>
   ```
   Sostituisci `<HOST>` e `<PORT>` con gli stessi valori usati per il server.

2. Scrivi messaggi nella console e premi **Invio** per inviarli.
3. Digita `{exit}` per disconnetterti.

## Requisiti
- **Python 3.7 o superiore.**
- Funzionante su Unix, macOS, Windows.

## Note
- Assicurati che il server sia in esecuzione prima di avviare i client.
- Testato con successo su sistemi Unix e Windows.
