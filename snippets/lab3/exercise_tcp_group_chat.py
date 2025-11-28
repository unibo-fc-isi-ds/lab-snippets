import sys

if __name__ == '__main__':
    try:
        port = sys.argv[1]
        print(port)
        endpoints = sys.argv[2:]
        print(endpoints)
    except IndexError as e:
        print(e)