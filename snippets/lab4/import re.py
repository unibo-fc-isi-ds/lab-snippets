import re

def escape_double_quotes(s):
    """
    Escapes unescaped double quotes in a string.
    """
    return re.sub(r'(?<!\\)"', '\\"', s)


if __name__ == '__main__':
    token = '''{
  "signature": "a0f68e4469b447a4e6a0c15cb274cf8be6fc2ccaa51789846951ac5effd1c265",
  "user": {
    "username": "gciatto",
    "emails": [
      "giovanni.ciatto@gmail.com",
      "giovanni.ciatto@unibo.it"
    ],
    "full_name": "Giovanni Ciatto",
    "role": {
      "name": "ADMIN",
      "$type": "Role"
    },
    "password": null,
    "$type": "User"
  },
  "expiration": {
    "datetime": "2024-11-27T16:13:36.566641",
    "$type": "datetime"
  },
  "$type": "Token"
}'''
print(token,"\n",escape_double_quotes(token))