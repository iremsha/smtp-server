import socket


def send_mail(mail_exchanger, data, recipient):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((mail_exchanger, 25))
        print(sock.recv(1024).decode())

        from smtp_server import send_command
        print(send_command(sock, b'EHLO ' + 'remsha.online'.encode()))
        print(send_command(sock, b'MAIL FROM:<' + 'ir@remsha.online'.encode() + b'>'))
        recipient = recipient.login
        print(send_command(sock, b'RCPT TO:<' + recipient.encode() + b'>'))
        send_command(sock, b'DATA')
        # prepared_message = self.prepare_message_text('Simple message')
        # msg = self.create_message(self.user_login, recipient, 'SMTP', prepared_message)
        # print(msg)
        # print(self.send_command(sock, msg.encode()))

        # print(data)
        print(send_command(sock, data.encode()))
