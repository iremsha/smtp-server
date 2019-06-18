import socket


def send_mail(mail_exchanger, data, recipient):
    throw_answer = ''
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect((mail_exchanger, 25))
        print(sock.recv(1024).decode())

        from smtp_server import send_command
        try:
            send_command(sock, b'EHLO ' + 'remsha.online'.encode())
            send_command(sock, b'MAIL FROM:<' + 'smtp@remsha.online'.encode() + b'>')
            recipient = recipient.login
            throw_answer += send_command(sock, b'RCPT TO:<' + recipient.encode() + b'>')
            throw_answer += send_command(sock, b'DATA')
            # prepared_message = self.prepare_message_text('Simple message')
            # msg = self.create_message(self.user_login, recipient, 'SMTP', prepared_message)
            # print(msg)
            # print(self.send_command(sock, msg.encode()))

            # print(data)
            throw_answer += send_command(sock, data.encode())
            if send_command(sock, b'QUIT'):
                sock.close()
                print('connection to forward server closed')
        except Exception as e:
            throw_answer += 'Error: {}'.format(e)

        finally:
            # Закрываем соеденинене с Сервером Форвардом и отправляем киленту его сообщения
            sock.close()
            print('Answer server:\n{}'.format(throw_answer))
            return throw_answer.encode()
