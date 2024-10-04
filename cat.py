import sys


BUFFER_SIZE = 1024


while True:
    chunk = sys.stdin.buffer.read(BUFFER_SIZE)
    if not chunk:
        break
    sys.stdout.buffer.write(chunk)
    sys.stdout.buffer.flush()
