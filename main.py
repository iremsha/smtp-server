import sys
from smtp_server import SMTPServer


def console_setting(key=''):
    print(key)


if __name__ == '__main__':
    if len(sys.argv) > 2:
        console_setting()

    if len(sys.argv) == 2:
        if sys.argv[1] in ('-h', '-help', '--help', '?', '-?'):
            console_setting(sys.argv[1])
        port = int(sys.argv[1])
    else:
        port = 25

    server = SMTPServer()
    print('server start')
    server.socket_accept()
