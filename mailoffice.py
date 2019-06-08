import base64
import resolver
import sender
from mailbox import Mailbox

import mimetypes
import email


def parse_data(data):
    print('-----------------------------')
    b = email.message_from_string(data)
    if b.is_multipart():
        print(b['From'])
        print(b['To'])
        print(b['Subject'])
        for payload in b.get_payload():
            # if payload.is_multipart(): ...
                print(payload.get_payload())
    print('-----------------------------')
    header = data[:data.find('MIME-Version: 1.0\n'):]
    # print(header)
    return '', '', '', ''


class MailOffice:
    def __init__(self, HOST):
        self.HOST = HOST
        self.forward = None
        self.recipient = None
        self.data = ''

    def do_data(self, data):
        self.detect_host(self.recipient.login)
        if self.our_client():
            '''Переименовать'''
            self.send_in_my_mailbox(data)
        else:
            print('Find Recipient SMTP')
            mail_exchanger = resolver.find_RR_MX(self.recipient.host)
            sender.send_mail(mail_exchanger, data, self.recipient)

    def detect_host(self, name):
        host = name[name.find('@') + 1:]
        self.recipient.host = host

    def our_client(self):
        return self.HOST == self.recipient.host

    def send_in_my_mailbox(self, data):
        forward, recipient, topic, text = parse_data(data)
        mailbox = Mailbox(self.recipient.login)
        mailbox.write_letter(forward, recipient, topic, text)


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
    '''