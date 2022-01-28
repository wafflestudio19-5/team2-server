from django.core.mail import EmailMessage
from celery import shared_task


@shared_task
def send_email_task(mail_title, message_data, mail_to):
    email = EmailMessage(mail_title, message_data, to=[mail_to])
    sent_message_count = email.send()
    print(sent_message_count)
    return sent_message_count