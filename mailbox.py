import datetime
import os

PATH = r'C:\Users\Remsha\Documents\GitHub\SMTP-Server\Mailbox\\'


def microtime(dt):
    unixtime = dt - datetime.datetime(1970, 1, 1)
    return unixtime.days * 24 * 60 * 60 + unixtime.seconds + unixtime.microseconds / 1000000.0


class Mailbox:
    def __init__(self, name):
        self.name = name
        self.path = PATH + self.name + '\\'
        self.create_mailbox()

    def create_mailbox(self):
        if not os.path.exists(self.path):
            os.makedirs(self.path)

    def write_letter(self, forward, recipient, topic, text):
        with open(self.path + topic + text + '.txt', 'w') as f:
            f.write(text)
