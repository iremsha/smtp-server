import base64
import socket
from client import Forward, Recipient
from mailoffice import MailOffice
LOCAL_HOST = 'remsha.online'


def send_command(sock, command, buffer=1024):
    sock.send(command + b'\n')
    return sock.recv(buffer).decode()


class SMTPServerCore:
    STATE_INIT = 0
    STATE_HELO = 1
    STATE_EHLO = 2
    STATE_MAIL = 3
    STATE_RCPT = 4
    STATE_DATA = 5
    STATE_QUIT = 6
    STATE_LOGIN = 7

    def __init__(self, conn):
        self.state = SMTPServerCore.STATE_INIT
        self.local_host = LOCAL_HOST
        self.socket = conn
        self.mail_office = MailOffice(LOCAL_HOST)
        self.forward = Forward()
        self.recipient = Recipient()

    def session(self):
        self.socket.send(b'220 mail.remsha.online SMTP is glad to see you!\n')
        while True:
            data = ''
            complete_line = 0

            while not complete_line:
                part = self.socket.recv(1024)
                part = part.decode()
                '''Мб убрать?'''
                if len(part):
                    data += part
                    '''Что это такое?'''
                    if len(data) >= 2:
                        complete_line = 1
                        if self.state != SMTPServerCore.STATE_DATA:
                            code = self.do_command(data)
                            print(code)
                        else:
                            code = self.mail_office.do_data(data)
                            if code is None:
                                continue
                        self.socket.send(code + b"\n")
                        '''if keep == 0:
                            self.socket.close()
                            return'''
                else:
                    # EOF
                    return

    def do_command(self, data):
        cmd = data[0:4]
        cmd = cmd.upper()
        info_log = ' {} '.format(cmd)

        if cmd == 'HELO':
            self.state = SMTPServerCore.STATE_HELO

        elif cmd == 'EHLO':
            self.state = SMTPServerCore.STATE_EHLO

        elif cmd == 'AUTH':
            self.state = SMTPServerCore.STATE_LOGIN

        elif cmd == "MAIL":
            self.forward.login = data[11:-2]
            info_log += self.forward.login
            ''''Пока что без авторизации'''
            # if self.state != SMTPServerCore.STATE_LOGIN:
            # return (b"503 Bad command sequence", 1)
            self.state = SMTPServerCore.STATE_MAIL

        elif cmd == "RCPT":
            if self.state != SMTPServerCore.STATE_MAIL:
                return b"503 Bad command sequence"
            self.recipient.login = data[9:-2]
            info_log += self.recipient.login
            self.state = SMTPServerCore.STATE_RCPT

        elif cmd == "DATA":
            if self.state != SMTPServerCore.STATE_RCPT:
                return b"503 Bad command sequence"
            self.state = SMTPServerCore.STATE_DATA
            self.mail_office.forward = self.forward
            self.mail_office.recipient = self.recipient
            self.data_accum = ""
            return b"354 OK, Enter data, terminated with a \\r\\n.\\r\\n"

        elif cmd == "QUIT":
            pass
            '''---------------------ОСНОВНОЙ БЛОК КОМАНД---------------------'''

        elif cmd == "RSET":
            self.data_accum = ""
            self.state = SMTPServerCore.STATE_INIT

        elif cmd == "NOOP":
            pass

        else:
            return b"505 Eh? WTF was that?"

        return b"250 OK" + info_log.encode()
    '''
    print(data)
    self.data_accum = self.data_accum + data
    if len(self.data_accum) > 4 and self.data_accum[-1] == '.':
        self.data_accum = self.data_accum[:-2]
        rv = self.impl.data(self.data_accum)
        print('Data pass')
        print(self.data_accum)
        self.state = SMTPServerCore.STATE_HELO
        if rv:
            return rv
        else:
            return b"250 OK - Data and terminator. found"
    else:
        return None
    '''


class SMTPServer:

    def __init__(self, port=25, listeners=5):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('0.0.0.0', port))
        self.socket.listen(listeners)

    def socket_accept(self):
        while True:
            conn, addr = self.socket.accept()
            engine = SMTPServerCore(conn)
            engine.session()


'''
#
# Some helper functions for manipulating from & to addresses etc.
#

def stripAddress(address):
    """
    Strip the leading & trailing <> from an address.  Handy for
    getting FROM: addresses.
    """
    start = string.index(address, '<') + 1
    end = string.index(address, '>')
    return address[start:end]


def splitTo(address):
    """
    Return 'address' as undressed (host, fulladdress) tuple.
    Handy for use with TO: addresses.
    """
    start = string.index(address, '<') + 1
    sep = string.index(address, '@') + 1
    end = string.index(address, '>')
    return (address[sep:end], address[start:end],)

'''

'''if self.state == SMTPServerCore.STATE_LOGIN:
                         try:
                             if not self.user_login:
                                 self.user_login = base64.b64decode(data.encode()).decode()
                             elif not self.user_password:
                                 self.user_password = base64.b64decode(data.encode()).decode()
                             elif self.user_login and self.user_password:
                                 self.detect_host(self.user_login)
                                 if self.in_my_part('remsha.online'):
                                     self.send_in_my_mailbox()
                                 else:
                                     mail_exchanger = self.find_his_smtp()
                                     self.send_mail(mail_exchanger)
                         except Exception as ex:
                             print('Ошибка: {}'.format(ex))'''