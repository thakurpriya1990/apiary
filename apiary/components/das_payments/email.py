import logging

from django.core.mail import EmailMultiAlternatives, EmailMessage
from django.utils.encoding import smart_text
from django.core.urlresolvers import reverse
from django.conf import settings

from apiary.components.emails.emails import TemplateEmailBase
from apiary.components.das_payments.invoice_pdf import create_invoice_pdf_bytes
from apiary.components.das_payments.confirmation_pdf import create_confirmation_pdf_bytes
from apiary.context_processors import apiary_url
from ledger.accounts.models import EmailUser

logger = logging.getLogger(__name__)

SYSTEM_NAME = settings.SYSTEM_NAME_SHORT + ' Automated Message'

def get_sender_user():
    sender = settings.DEFAULT_FROM_EMAIL
    try:
        sender_user = EmailUser.objects.get(email__icontains=sender)
    except:
        EmailUser.objects.create(email=sender, password='')
        sender_user = EmailUser.objects.get(email__icontains=sender)
    return sender_user

class ApplicationFeeInvoiceApiarySendNotificationEmail(TemplateEmailBase):
    subject = 'Your application fee invoice.'
    html_template = 'disturbance/emails/payments/apiary/send_application_fee_notification.html'
    txt_template = 'disturbance/emails/payments/apiary/send_application_fee_notification.txt'

# not required
#class ApplicationFeeConfirmationApiarySendNotificationEmail(TemplateEmailBase):
#    subject = 'Your application fee confirmation.'
#    html_template = 'disturbance/emails/payments/apiary/send_application_fee_confirmation_notification.html'
#    txt_template = 'disturbance/emails/payments/apiary/send_application_fee_confirmation_notification.txt'


def send_application_fee_invoice_apiary_email_notification(request, proposal, invoice, recipients, is_test=False):
    email = ApplicationFeeInvoiceApiarySendNotificationEmail()
    #url = request.build_absolute_uri(reverse('external-proposal-detail',kwargs={'proposal_pk': proposal.id}))

    url_var = apiary_url(request)
    context = {
        'lodgement_number': proposal.lodgement_number,
        #'url': url,
    }

    filename = 'invoice#{}.pdf'.format(invoice.reference)
    doc = create_invoice_pdf_bytes(filename, invoice, url_var, proposal)
    attachment = (filename, doc, 'application/pdf')

    msg = email.send(recipients, attachments=[attachment], context=context)
    if is_test:
        return

    #sender = request.user if request else settings.DEFAULT_FROM_EMAIL
    sender = get_sender_user()
    _log_proposal_email(msg, proposal, sender=sender)
#    try:
#        _log_org_email(msg, proposal.applicant, proposal.submitter, sender=sender)
#    except:
#        _log_org_email(msg, proposal.submitter, proposal.submitter, sender=sender)
    if proposal.applicant:
        _log_org_email(msg, proposal.applicant, proposal.submitter, sender=sender)
    else:
        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)

# not required
#def send_application_fee_confirmation_apiary_email_notification(request, application_fee, invoice, recipients, is_test=False):
#    email = ApplicationFeeConfirmationApiarySendNotificationEmail()
#    #url = request.build_absolute_uri(reverse('external-proposal-detail',kwargs={'proposal_pk': proposal.id}))
#
#    proposal = application_fee.proposal
#    context = {
#        'lodgement_number': proposal.lodgement_number,
#        #'url': url,
#    }
#
#    filename = 'confirmation.pdf'
#    doc = create_confirmation_pdf_bytes(filename, invoice, application_fee)
#    #doc = create_invoice_pdf_bytes(filename, invoice, proposal)
#    attachment = (filename, doc, 'application/pdf')
#
#    msg = email.send(recipients, attachments=[attachment], context=context)
#    if is_test:
#        return
#
#    sender = request.user if request else settings.DEFAULT_FROM_EMAIL
#    _log_proposal_email(msg, proposal, sender=sender)
#    if proposal.applicant:
#        _log_org_email(msg, proposal.applicant, proposal.submitter, sender=sender)
#    else:
#        _log_user_email(msg, proposal.submitter, proposal.submitter, sender=sender)


def _log_proposal_email(email_message, proposal, sender=None):
    from apiary.components.proposals.models import ProposalLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = proposal.submitter.email
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = proposal.submitter

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'proposal': proposal,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = ProposalLogEntry.objects.create(**kwargs)

    return email_entry


def _log_org_email(email_message, organisation, customer ,sender=None):
    from apiary.components.organisations.models import OrganisationLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = customer
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = customer

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'organisation': organisation,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = OrganisationLogEntry.objects.create(**kwargs)

    return email_entry


def _log_user_email(email_message, emailuser, customer ,sender=None):
    from ledger.accounts.models import EmailUserLogEntry
    if isinstance(email_message, (EmailMultiAlternatives, EmailMessage,)):
        # TODO this will log the plain text body, should we log the html instead
        text = email_message.body
        subject = email_message.subject
        fromm = smart_text(sender) if sender else smart_text(email_message.from_email)
        # the to email is normally a list
        if isinstance(email_message.to, list):
            to = ','.join(email_message.to)
        else:
            to = smart_text(email_message.to)
        # we log the cc and bcc in the same cc field of the log entry as a ',' comma separated string
        all_ccs = []
        if email_message.cc:
            all_ccs += list(email_message.cc)
        if email_message.bcc:
            all_ccs += list(email_message.bcc)
        all_ccs = ','.join(all_ccs)

    else:
        text = smart_text(email_message)
        subject = ''
        to = customer
        fromm = smart_text(sender) if sender else SYSTEM_NAME
        all_ccs = ''

    customer = customer

    staff = sender

    kwargs = {
        'subject': subject,
        'text': text,
        'emailuser': emailuser,
        'customer': customer,
        'staff': staff,
        'to': to,
        'fromm': fromm,
        'cc': all_ccs
    }

    email_entry = EmailUserLogEntry.objects.create(**kwargs)

    return email_entry
