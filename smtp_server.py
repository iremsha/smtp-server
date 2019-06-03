import base64
import datetime
import json
import socket
import string
import sys
from subprocess import Popen, PIPE


class SMTPServerInterface:

    def __init__(self):
        self._from = ''
        self.to = ''
        self.body = ''

    def helo(self, args):
        return None

    def ehlo(self, args):
        return None

    def auth(self, args):
        return None

    def mail_from(self, args):
        self._from = args.replace('\r\n', '').replace('MAIL FROM:', '')
        return None

    def rcpt_to(self, args):
        self.to = args.replace('\r\n', '').replace('RCPT TO:', '')
        return None

    def data(self, args):
        self.body = args
        return None

    # write mail to file, filename - microtime, data - json serialized
    def quit(self, args):
        f = open(str(microtime(datetime.datetime.now())) + '.json.pymail', 'w')
        f.write(json.dumps({'from': self._from, 'to': self.to, 'body': self.body}, separators=(',', ':')))
        f.close()
        return None

    def reset(self, args):
        return None


#
# Some helper functions for manipulating from & to addresses etc.
#
def microtime(dt):
    unixtime = dt - datetime.datetime(1970, 1, 1)
    return unixtime.days * 24 * 60 * 60 + unixtime.seconds + unixtime.microseconds / 1000000.0


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


#
# A specialization of SMTPServerInterface for debug, that just prints its args.
#
class SMTPServerInterfaceDebug(SMTPServerInterface):
    """
    A debug instance of a SMTPServerInterface that just prints its
    args and returns.
    """

    def helo(self, args):
        print()
        'Received "helo"', args.replace('\n', '')
        SMTPServerInterface.helo(self, args)

    def ehlo(self, args):
        print()
        'Received "ehlo"', args.replace('\n', '')
        SMTPServerInterface.ehlo(self, args)

    def auth(self, args):
        print()
        'Received "AUTH LOGIN:"', args.replace('\n', '')
        SMTPServerInterface.auth(self, args)

    def mail_from(self, args):
        print(args)
        'Received "MAIL FROM:"', args.replace('\n', '')
        SMTPServerInterface.mail_from(self, args)

    def rcpt_to(self, args):
        SMTPServerInterface.rcpt_to(self, args)
        print()
        'Received "RCPT TO"', args.replace('\n', '')

    def data(self, args):
        SMTPServerInterface.data(self, args)
        print()
        'Received "DATA", skipped'

    def quit(self, args):
        SMTPServerInterface.quit(self, args)
        print()
        'Received "QUIT"', args.replace('\n', '')

    def reset(self, args):
        SMTPServerInterface.reset(self, args)
        print()
        'Received "RSET"', args.replace('\n', '')


class SMTPServerCore:
    STATE_INIT = 0
    STATE_HELO = 1
    STATE_EHLO = 2
    STATE_MAIL = 3
    STATE_RCPT = 4
    STATE_DATA = 5
    STATE_QUIT = 6
    STATE_LOGIN = 7

    def __init__(self, socket, impl):
        self.impl = impl
        self.socket = socket
        self.state = SMTPServerCore.STATE_INIT
        self.user_login = ''
        self.user_password = ''
        self.recipient = ''
        self.user_host = ''
        self.recipient_host = ''
        self.local_host = 'remsha.online'
        self.default_smtp = 'mx.yandex.ru'

    def work_session(self):

        self.socket.send(b'220 Welcome\n It is My SMTP Server.')
        while 1:
            data = ''
            complete_line = 0

            while not complete_line:
                part = self.socket.recv(1024)
                part = part.decode()
                if len(part):
                    data += part
                    '''Что это такое?'''
                    if len(data) >= 2:
                        complete_line = 1
                        if self.state == SMTPServerCore.STATE_LOGIN:
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
                                print('Ошибка: {}'.format(ex))
                        '''Если не данные то.. отправляем то, что прочитали. Иначе принимаем данные'''
                        if self.state != SMTPServerCore.STATE_DATA:
                            rsp, keep = self.do_command(data)
                            print(rsp)
                        else:
                            rsp = self.do_data(data)
                            if rsp is None:
                                continue
                        self.socket.send(rsp + b"\n")
                        if keep == 0:
                            self.socket.close()
                            return
                else:
                    # EOF
                    return
        return

    def detect_host(self, host):
        host = host[host.find('@') + 1:]
        self.user_host = host
        return host

    def in_my_part(self, my_host):
        print(my_host, 1)
        print(self.recipient_host, 2)
        return my_host == self.recipient_host

    def do_command(self, data):
        cmd = data[0:4]
        cmd = cmd.upper()
        keep = 1
        rv = None
        if cmd == 'HELO':
            self.state = SMTPServerCore.STATE_HELO
            ''''Тупо бесполезная штука'''
            rv = self.impl.helo(data)
        elif cmd == 'EHLO':
            self.state = SMTPServerCore.STATE_EHLO
            ''''Тупо бесполезная штука - Вернёт None'''
            rv = self.impl.ehlo(data)
        elif cmd == 'AUTH':
            rv = self.impl.auth(data)
            self.state = SMTPServerCore.STATE_LOGIN
        elif cmd == "MAIL":
            self.user_login = data[11:-2]
            ''''Пока что без авторизации'''
            # if self.state != SMTPServerCore.STATE_LOGIN:
            # return (b"503 Bad command sequence", 1)
            self.state = SMTPServerCore.STATE_MAIL
            rv = self.impl.mail_from(data)
        elif cmd == "RCPT":
            self.recipient = data[9:-2]
            if self.state != SMTPServerCore.STATE_MAIL:  # and (self.state != SMTPServerCore.STATE_RCPT):
                return b"503 Bad command sequence", 1
            self.state = SMTPServerCore.STATE_RCPT
            rv = self.impl.rcpt_to(data)
        elif cmd == "DATA":
            if self.state != SMTPServerCore.STATE_RCPT:
                return b"503 Bad command sequence", 1
            self.state = SMTPServerCore.STATE_DATA
            self.data_accum = ""
            return b"354 OK, Enter data, terminated with a \\r\\n.\\r\\n", 1
        elif cmd == "QUIT":
            rv = self.impl.quit(data)
            keep = 0
            '''---------------------ОСНОВНОЙ БЛОК КОМАНД---------------------'''
        elif cmd == "RSET":
            rv = self.impl.reset(data)
            self.data_accum = ""
            self.state = SMTPServerCore.STATE_INIT
        elif cmd == "NOOP":
            pass
        else:
            return (b"505 Eh? WTF was that?", 1)

        '''Что это?'''
        if rv:
            return (rv, keep)
        else:
            return (b"250 OK", keep)

    def do_data(self, data):
        host = self.detect_host(self.recipient)
        if self.in_my_part('remsha.online'):
            self.send_in_my_mailbox()
        else:
            print('Письмо не в мой ящик!')
            mail_exchanger = self.find_his_smtp(host)
            self.send_mail(mail_exchanger)
            print('заебумба')

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
    def send_in_my_mailbox(self):
        pass

    def find_his_smtp(self, hots):
        with Popen(['nslookup', "-type=MX", hots], stdout=PIPE) as cmd:
            answer = cmd.stdout.read().decode('cp1256')
            _MX_record = answer.split('\n')[3]
            idx = _MX_record.find('mail exchanger = ')
            mail_exchanger = _MX_record[idx + len('mail exchanger = '):-1]
        return mail_exchanger

    def send_mail(self, mail_exchanger):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect((mail_exchanger, 25))
            print('dead')
            print(sock.recv(1024).decode())
            print(self.send_command(sock,
                                    b'EHLO ' + self.local_host.encode()))
            print(self.send_command(sock, b'MAIL FROM:<' + 'ir@remsha.online'.encode() + b'>'))
            recipient = self.recipient
            print(self.send_command(sock, b'RCPT TO:<' + recipient.encode() + b'>'))
            self.send_command(sock, b'DATA')
            prepared_message = self.prepare_message_text('Simple message')
            print('mail from:', self.user_login)
            msg = self.create_message(self.user_login, recipient, 'SMTP', prepared_message)
            print(msg)
            print(self.send_command(sock, msg.encode()))

    '''
    def send(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.connect(('smtp.yandex.ru', 465))
            print(sock.recv(1024).decode())  # Вычитываем что-то там, на 1 опаздываем
            print(self.send_command(sock,
                                    b'EHLO remsha.online'))  # Разница HELO EHLO, почему одна L // КОДЫ КОМАНД 250 - хорошо
            print(self.send_command(sock, b'MAIL FROM:' + self.login.encode()))
            recipient = self.login  # Получатель
            print(self.send_command(sock, b'RCPT TO:' + recipient.encode()))
            self.send_command(sock, b'DATA')
            prepared_message = self.prepare_message_text('Simple message')
            msg = self.create_message(self.login, recipient, 'SMTP', prepared_message)
            print(msg)
            print(self.send_command(sock, msg.encode()))
    '''
    def create_message(self, login, recipient, theme, message_text):  # attachment
        BOUNDARY = 0
        return (
            f'From: {login}\n'
            f'To: {recipient}\n'
            f'MIME-Version: 1.0\n'
            f'Subject: {theme}\n'
            f'Content-Type: multipart/mixed;; boundary="{BOUNDARY}"\n\n'
            f'--{BOUNDARY}\n'
            f'Content-Transfer-Encoding: 8bit\n'
            f'Content-Type: text/html; charset=utf-8\n\n'
            f'{message_text}\n'
            # f'{attachment}\n' 
            f'--{BOUNDARY}--\n'
            f'.'
        )

    def handle_attachment(self, files):
        result_attachment = '' \
                            ''
        for file in files:
            splited_name = file.split(' ')
            extension = splited_name[-1]
            with open(file, 'rb') as f:
                encoded_file = base64.b64encode(f.read())
                # mime_type = MIME_TYPES[extension] # Завести лист с типами
                result_attachment.append(
                    (f'Content-Disposition: attachment;'
                     f'	filename="{file}"')
                )

    def prepare_message_text(self, message):
        return message

    def send_command(self, sock, command, buffer=1024):
        sock.send(command + b'\n')
        return sock.recv(buffer).decode()


class SMTPServer:

    def __init__(self):
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.socket.bind(('0.0.0.0', 3122))
        self.socket.listen(5)

    def wait_connection(self, impl=None):
        while 1:
            conn, addr = self.socket.accept()
            print(conn, addr)
            if impl is None:
                ''''Now i don't know why this is Interface'''
                impl = SMTPServerInterfaceDebug()
            engine = SMTPServerCore(conn, impl)
            engine.work_session()


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
    s = SMTPServer()
    print('Server Start')
    s.wait_connection()
