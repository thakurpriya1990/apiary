from django.utils.encoding import smart_bytes
from django.core.mail import EmailMultiAlternatives, EmailMessage
from apiary.settings import SYSTEM_NAME


def _extract_email_headers(email_message, sender=None):
    print(sender)
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html
        # instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_bytes(sender) if sender else smart_bytes(
            email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_bytes(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ','
        # comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_bytes(email_message)
        subject = ''
        to = ''
        fromm = smart_bytes(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    email_data = {
        'subject': subject,
        'text': text,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    return email_data
