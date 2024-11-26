# [A.Y. 2024/2025 Galeri, Marco] Exercise: Secure RPC Auth Service

## Descrizione della Soluzione per il servizio di autenticazione

La soluzione proposta implementa il servizio di autenticazione aggiungendo la classe `InMemoryAuthenticationService` al `Server Stub` insieme ad un match sul nome delle *Request* per gestire le chiamate, inoltre ho modificato anche il `Client Stub` per offrire un interfaccia alle nuove funzionalità di autenticazione e finito di scrivere il serializzatore per il tipo `datetime` usato nei token.


---

## Descrizione della Soluzione per il servizio di autorizzazione

La soluzione proposta modifica la classe `Request` aggiungendo un campo opzionale `token`, per questo ho modificato il serializzatore in modo da gestire la serializzazione di entrambe le richieste.\
Nel `Server Stub` ho ulteriormente diramato il match sul nome delle richieste aggiungendo un controllo sul token e il ruolo dell'utente.\
Nel `Client Stub` ho aggiunto un campo per memorizzare il token ed infine per l'utilizzo tramite una interfaccia da riga di comando ho implementato due funzioni per salvare e leggere dalla memoria il token ricevuto. Per comodità il file viene salvato in chiaro nella cartella del laboratorio.

---