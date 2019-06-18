import base64
import codecs
import os
from email.header import decode_header
import resolver
import sender
from mailbox import Mailbox
import email
import re
from mailbox import PATH

PATH_ATTACHMENT = os.path.join(PATH, 'attachment')
PATH_LETTERS = os.path.join(PATH, 'letters')


def parse_simple_letter(mail):
    """
    Парсим простое письмо, если в нейм нет Бордеров.
    :param mail:
    :return:
    """
    mail = mail[mail.find('\n\n')+2:]
    return clean_html(mail)


def decode_image(data):
    """
    Декодируем изображение и записываем его в фаил.
    :param data:
    :return:
    """
    name = data[14:21]
    data = base64.b64decode(data)
    with open(os.path.join(PATH_ATTACHMENT, name + '.png'), 'wb') as f:
        f.write(data)
    print('Done image')


def decode_audio(data):
    name = data[14:21]
    data = base64.b64decode(data)
    with open(os.path.join(PATH_ATTACHMENT, name + '.mp3'), 'wb') as f:
        f.write(data)
    print('Done audio')


def decode_pdf(data):
    name = data[14:21]
    data = base64.b64decode(data)
    with open(os.path.join(PATH_ATTACHMENT, name + '.pdf'), 'wb') as f:
        f.write(data)
    print('Done pdf')


def clean_header(mail_obj):
    """
    Убираем закодированные доп. заголовки которые прикрутил отправитель.
    :param mail_obj:
    :return:
    """
    answer = ''
    obj = decode_header(mail_obj)
    len_obj = len(obj)
    for i in range(len_obj):
        text = obj[i][0]
        code = obj[i][1]
        if code:
            text = codecs.decode(text, code)
        elif isinstance(text, bytes):
            text = text.decode()
        answer += text
    print(answer)
    return answer


def clean_html(raw_html):
    """
    Извлекаем текст из HTML-тегов. (Яндекс отправляет с тегами)
    :param raw_html:
    :return:
    """
    clean_l = re.compile('<.*?>')
    clean_text = re.sub(clean_l, '', raw_html)
    print(clean_text)
    return clean_text


def parse_data(data):
    """
    Разбираем поступившие данные, получаем все заголовки и тело письма.
    :param data: данный, что нам передали (для тестов данные беру из файла).
    :return:
    """

    # Тестим то, как декодируются сообщения
    print(PATH_LETTERS)
    with open(os.path.join(PATH_LETTERS, 'mail_test_main.txt'), 'r') as f:
        data = f.read()

    mail_from, mail_to, mail_subject, mail_body, mail_date = '', '', '', '', ''
    mail = email.message_from_string(data)
    mail_from = clean_header(mail['From'])
    mail_to = clean_header(mail['To'])
    try:
        mail_subject = clean_header(mail['Subject'])
        mail_date = clean_header(mail['Date'])
    except TypeError as e:
        pass

    if mail.is_multipart():
        for payload in mail.get_payload():
            # if payload.is_multipart():
                mail_body = payload.get_payload()
                if not mail_body:
                    parse_simple_letter(data)

        """Для Атачмента"""
        for part in mail.walk():
            ctype = part.get_content_type()

            if ctype == 'image/jpeg':
                body = part.get_payload()
                decode_image(body)
            elif ctype == 'text/html':
                body = part.get_payload()
                mail_body = clean_html(body)
            elif ctype == 'audio/mpeg':
                body = part.get_payload()
                decode_audio(body)
            elif ctype == 'application/pdf':
                body = part.get_payload()
                decode_pdf(body)



    else:
        # Если это было обычное письмо без раздение на части
        mail_body = parse_simple_letter(data)
    return mail_from, mail_to, mail_subject, mail_body


class MailOffice:
    def __init__(self, HOST):
        self.HOST = HOST
        self.forward = None
        self.recipient = None
        self.data = ''

    def do_data(self, data):
        data = data.decode()
        self.detect_host(self.recipient.login)
        if self.our_client():
            '''Переименовать'''
            self.send_in_my_mailbox(data)
        else:
            print('Find Recipient SMTP')
            mail_exchanger = resolver.find_RR_MX(self.recipient.host)
            return sender.send_mail(mail_exchanger, data, self.recipient)

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
