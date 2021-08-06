import datetime
import os

dirname = os.path.dirname('SMTP-Server')
PATH = os.path.join(dirname, 'src')


def microtime(dt):
    unixtime = dt - datetime.datetime(1970, 1, 1)
    return unixtime.days * 24 * 60 * 60 + unixtime.seconds + unixtime.microseconds / 1000000.0


def set_letter(forward, recipient, topic, text):
    letter_body = 'Mail from: {0}\n' \
                  'Mail to: {1}\n' \
                  'Subject: {2}\n\n' \
                  '{3}\n\n'\
                  'Data: {4}'.format(forward, recipient, topic, text, datetime.datetime.now())
    return letter_body


class Mailbox:
    def __init__(self, name):
        self.name = name
        # self.path = PATH + self.name + '\\'
        self.path = os.path.join(PATH, self.name)
        self.create_mailbox()

    def create_mailbox(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def write_letter(self, forward, recipient, topic, text):
        letter = set_letter(forward, recipient, topic, text)
        with open(os.path.join(self.path, topic + '.txt'), 'w') as f:
            f.write(letter)

