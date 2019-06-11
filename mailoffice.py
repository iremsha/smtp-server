import base64
import resolver
import sender
from mailbox import Mailbox
import email

temp_part_counter = 0


def parse_data(data):
    with open('test.txt', 'r') as f:
        data = f.read()
    global temp_part_counter
    mail_from, mail_to, mail_subject, mail_body = '', '', '', ''
    mail_end = False
    temp_part_counter += 1
    print('-----------------------------')
    mail = email.message_from_string(data)
    '''if mail.is_multipart():
        mail_from = mail['From']
        mail_to = mail['To']
        mail_subject = mail['Subject']
        for payload in mail.get_payload():
            # if payload.is_multipart(): ...
                mail_body = payload.get_payload()
                if mail_body[-1] == ".":
                    mail_end = True
    print(temp_part_counter)
    print('-----------------------------')'''

    if mail.is_multipart():
        print('+++++++++++++++++++++++++')
        for part in mail.walk():
            ctype = part.get_content_type()
            #print(ctype)
            cdispo = str(part.get('Content-Disposition'))
            #print(cdispo)

            # skip any text/plain (txt) attachments
            #if ctype == 'text/plain' and 'attachment' not in cdispo:
            if ctype == 'image/jpeg':
                body = part.get_payload()  # decode
                print(body)
            #break
    # not multipart - i.e. plain text, no attachments, keeping fingers crossed
    else:
        body = mail.get_payload(decode=True)

    return mail_from, mail_to, mail_subject, mail_body


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
        forward, recipient, topic, body = parse_data(data)
        if body:
            mailbox = Mailbox(self.recipient.login)
            mailbox.write_letter(forward, recipient, topic, body)


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