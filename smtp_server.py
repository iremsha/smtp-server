import threading
import socket
from client import Forward, Recipient
from mailoffice import MailOffice


LOCAL_HOST = 'remsha.online'


def send_command(sock, command, buffer=1024):
    """
    Отправляем команду SMTP-Serve-y получателя или клиенту.
    :param sock:
    :param command:
    :param buffer:
    :return: Прочитанный ответ
    """
    sock.sendall(command + b'\n')
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
        """
        Главный цикл общения сервера и клиента.
        :return:
        """
        self.socket.sendall(b'220 mail.remsha.online SMTP is glad to see you!\n')
        while True:
            data = bytearray()
            complete_line = 0

            while not complete_line:
                part = self.socket.recv(1024)
                if part:
                    data += part
                    if len(data) >= 2:
                        complete_line = 1
                        if self.state != SMTPServerCore.STATE_DATA:
                            code, keep_connection = self.do_command(data)
                            print(code)
                        else:
                            code = self.mail_office.do_data(data)
                            keep_connection = 1
                            if code is None:
                                continue
                        self.socket.sendall(code + b"\n")
                        if not keep_connection:
                            self.socket.close()
                else:
                    # EOF
                    return

    def do_command(self, data):
        """
        Разбираем команду которую получили от клиента и меняем состояние сервера, возвращаем код операции.
        :param data:
        :return:
        """
        data = data.decode()
        cmd = data[0:4]
        cmd = cmd.upper()
        keep_connection = 1
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
                return b"503 Bad command sequence", 0
            self.recipient.login = data[9:-2]
            info_log += self.recipient.login
            self.state = SMTPServerCore.STATE_RCPT

        elif cmd == "DATA":
            if self.state != SMTPServerCore.STATE_RCPT:
                return b"503 Bad command sequence", 0
            self.state = SMTPServerCore.STATE_DATA
            self.mail_office.forward = self.forward
            self.mail_office.recipient = self.recipient
            return b"354 OK, Enter data, terminated with a \\r\\n.\\r\\n", keep_connection

        elif cmd == "QUIT":
            return b"221 remsha.online Service closing ", 0

        elif cmd == "RSET":
            self.state = SMTPServerCore.STATE_INIT

        elif cmd == "NOOP":
            return b"250 I Can Fly", keep_connection


        else:
            return b"505 Bad command", 0

        return b"250 OK" + info_log.encode(), keep_connection


class SMTPServer:

    def __init__(self, port=25, listeners=5):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('0.0.0.0', port))
        self.socket.listen(listeners)

    def socket_accept(self):
        while True:
            conn, addr = self.socket.accept()
            engine = SMTPServerCore(conn)
            t = threading.Thread(target=engine.session())
            t.start()


'''

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