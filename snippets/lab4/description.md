# Lab4 — Heisenberg RPC CLI commands and example outputs (Markdown)

This file collects the exact commands and example outputs for the **Heisenberg** user scenario (RPC server on port `14000`). You can copy/paste the commands directly into your terminal. Text files mentioned are under `outputs/`.

---

## 00 — Prepared outputs folder in the lab dir

```bash
mkdir -p outputs
```

---

## 01 — Start server (Terminal A)

Run this in Terminal A and keep it open:

```bash
poetry run python -u -m snippets.lab4.example2_rpc_server 14000
```

Screenshot name: `outputs/lab4-03-server-listening.png`

---

## 02 — Add user `heisenberg` (Terminal B)

Command (copy/paste):

```bash
poetry run python -u -m snippets.lab4.example4_rpc_client_cli 127.0.0.1:14000 add \
  -u heisenberg -a heisenberg@studio.unibo.it -n "Heisenberg" -p SayMyName12345 --role user
```

Example client output to screenshot / save (your actual signature / timestamps will differ):

```
poetry run python -u -m snippets.lab4.example4_rpc_client_cli 127.0.0.1:14000 add \
  -u heisenberg -a heisenberg@studio.unibo.it -n "Heisenberg" -p SayMyName12345 --role user
# Connected to 127.0.0.1:14000
# Marshalling Request(name='add_user', args=(User(username='heisenberg', emails={'heisenberg@studio.unibo.it'}, full_name='Heisenberg', role=<Role.USER: 2>, password='SayMyName12345'),)) towards 127.0.0.1:14000
# Sending message: {
#   "name": "add_user",
#   "args": [
#     {
#       "username": "heisenberg",
#       "emails": [
#         "heisenberg@studio.unibo.it"
#       ],
#       "full_name": "Heisenberg",
#       "role": {
#         "name": "USER",
#         "$type": "Role"
#       },
#       "password": "SayMyName12345",
#       "$type": "User"
#     }
#   ],
#   "$type": "Request"
# }
# Received message: {
#   "result": null,
#   "error": null,
#   "$type": "Response"
# }
# Unmarshalled Response(result=None, error=None) from 127.0.0.1:14000
# Disconnected from 127.0.0.1:14000
None
(lab-snippets-py3.11) rakymzhan@192 lab-snippets %
```

Server-side snippet you can screenshot (Terminal A):

```
[127.0.0.1:XXXXX] Open connection
[127.0.0.1:XXXXX] Unmarshall request: Request(name='add_user', args=(User(username='heisenberg', emails={'heisenberg@studio.unibo.it'}, full_name='Heisenberg', role=<Role.USER: 2>, password='SayMyName12345'),))
Add: User(username='heisenberg', emails={'heisenberg@studio.unibo.it'}, full_name='Heisenberg', role=<Role.USER: 2>, password='<hashed>')
[127.0.0.1:XXXXX] Marshall response: Response(result=None, error=None)
[127.0.0.1:XXXXX] Close connection
```

---

## 03 — Get user `heisenberg`

**Note:** the CLI requires `--user` (not a positional argument).

Command:

```bash
poetry run python -u -m snippets.lab4.example4_rpc_client_cli 127.0.0.1:14000 get --user heisenberg
```

Example output:

```
# Connected to 127.0.0.1:14000
# Marshalling Request(name='get_user', args=('heisenberg',)) towards 127.0.0.1:14000
# Sending message: {
#   "name": "get_user",
#   "args": [
#     "heisenberg"
#   ],
#   "$type": "Request"
# }
# Received message: {
#   "result": {
#     "username": "heisenberg",
#     "emails": [
#       "heisenberg@studio.unibo.it"
#     ],
#     "full_name": "Heisenberg",
#     "role": {
#       "name": "USER",
#       "$type": "Role"
#     },
#     "password": null,
#     "$type": "User"
#   },
#   "error": null,
#   "$type": "Response"
# }
# Unmarshalled Response(result=User(username='heisenberg', emails={'heisenberg@studio.unibo.it'}, full_name='Heisenberg', role=<Role.USER: 2>, password=None), error=None) from 127.0.0.1:14000
# Disconnected from 127.0.0.1:14000
User(username='heisenberg', emails={'heisenberg@studio.unibo.it'}, full_name='Heisenberg', role=<Role.USER: 2>, password=None)
```

---

## 04 — Check password

Command:

```bash
poetry run python -u -m snippets.lab4.example4_rpc_client_cli 127.0.0.1:14000 check --user heisenberg --password SayMyName12345 
```

Expected output: `True`

---

## 05 — Authenticate (get token JSON)

Command:

```bash
poetry run python -u -m snippets.lab4.example4_rpc_client_cli 127.0.0.1:14000 auth --user heisenberg --password SayMyName12345
```

Example output (token values will vary):

```
Token(user=User(username='heisenberg', emails={'heisenberg@studio.unibo.it'}, full_name='Heisenberg', role=<Role.USER: 2>, password=None), expiration=datetime.datetime(2025, 12, 30, 23, 59, 59, 123456), signature='PLACEHOLDER_SIGNATURE')
Serialized token:
{
  "signature": "PLACEHOLDER_SIGNATURE",
  "user": {
    "username": "heisenberg",
    "emails": [
      "heisenberg@studio.unibo.it"
    ],
    "full_name": "Heisenberg",
    "role": {
      "name": "USER",
      "$type": "Role"
    },
    "password": null,
    "$type": "User"
  },
  "expiration": {
    "value": "2025-12-30T23:59:59.123456"
  },
  "$type": "Token"
}
```

Extract the serialized JSON block to a token file:

```bash
sed '1d' > outputs/lab4-06-token-heisenberg.json
```

---

## 06 — Validate token

Command (use the saved JSON to avoid shell quoting issues):

```bash
poetry run python -u -m snippets.lab4.example4_rpc_client_cli 127.0.0.1:14000 validate -t "$(cat outputs/lab4-06-token-heisenberg.json)"
```

Expected output: `True`

---

## 07 — Tamper token

Make a copy and change the signature in the JSON to check validation fails:

```bash
cp outputs/lab4-06-token-heisenberg.json outputs/lab4-08-token-tampered-heisenberg.json
# edit outputs/lab4-08-token-tampered-heisenberg.json: change the signature value to "tampered-signature"
poetry run python -u -m snippets.lab4.example4_rpc_client_cli 127.0.0.1:14000 validate -t "$(cat outputs/lab4-08-token-tampered-heisenberg.json)"
```

Expected output: `False`

---

## Quick notes & tips

* `get`, `check`, `auth` require `--user` (no positional username). `add` supports `-u` and `-a` flags.
* If the `add` or `get` commands return an error about "already exists" or "not found" that is server-side behavior and expected when testing duplicate adds or missing users.