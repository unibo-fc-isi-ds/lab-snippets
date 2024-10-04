import random


try:
    while True:
        print(random.randint(-2**31, 2**31 - 1))
except (KeyboardInterrupt, EOFError, BrokenPipeError):
    pass
