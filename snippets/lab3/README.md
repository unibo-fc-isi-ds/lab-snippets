# [A.Y. 2024/2025 Galeri, Marco] Exercise: TCP Group Chat

### Descrizione della Soluzione di Chat di Gruppo in TCP

La soluzione proposta implementa una chat di gruppo basata sul protocollo TCP in cui non è più presente il ruolo di **server** e di **client** ma ogni utente svolge entrambi i ruoli contemporaneamente.

---

### Architettura

L’architettura si basa su una gestione peer-to-peer, dove ogni partecipante alla chat può comunicare con gli altri tramite connessioni TCP dirette.
 - Ogni peer è rappresentato da un oggetto `GroupPeer` che è composto da un oggetto `Server` ed una lista di oggetti `Client` che funzionano in questo modo:
     - `Server`: ascolta sulla porta selezionata ed accetta nuove connessioni e le registra come peer.
     - `Client`: stabilisce connessioni verso altri peer e invia messaggi.

---

### Gestione delle Disconnessioni

Quando un utente decide di uscire dalla chat, viene inviato un messaggio codificato con il codice `<EXITENCD>` agli altri peer per notificarli della disconnessione.\
Questo permette a chi lo riceve di aggiornare correttamente la lista dei peer attivi, evitando messaggi inviati a connessioni non più valide.

---

### Gestione dei Messaggi

- **Invio dei Messaggi**: 
  I messaggi vengono inviati a tutti i peer connessi utilizzando il metodo `broadcast_message`. Ogni messaggio è formattato con timestamp, nome del mittente e contenuto.\
  Per evitare problemi di Injection alla fine di ogni messaggio viene aggiunto il codice `<MSGENCD>` alla fine di ogni messaggio. 
  
- **Ricezione Asincrona**:
  La ricezione dei messaggi è gestita tramite thread separati. In base al codice in coda al messaggio il thread in ricezione esegue in event-matching ed esegue la stampa del messaggio ricevuto o in caso di un messaggio di disconnessione rimuove l'indirizzo dalla lista dei peer e stampa il messaggio predefinito di uscita.

---

### Funzionalità

- **Avvio del programma**:
  Per l'avvio del programma dati problemi di compilazione che non sono riuscito a comprendere ho riutilizzato lo script già presente nella repo.
  Quindi dopo aver attivato il Virtual Enviroment e si lancia il comando qua sotto specificando la porta di ascolto e gli indirizzi dei peer da connettere se presenti :
  ```bash
  poetry run python -m snippets --lab 3 --example 4 <porta> <peer1>:<porta1>
  ```
- **Uso della chat**:
  - Inserire un messaggio e premere Invio per inviarlo.
  - Uscire dalla chat con `Ctrl+D` o `Ctrl+C`.

---