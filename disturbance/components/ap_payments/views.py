from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.base import View, TemplateView
from django.db import transaction
from django.core.exceptions import PermissionDenied

from datetime import datetime
from ledger_api_client.ledger_models import EmailUserRO as EmailUser

from disturbance.components.approvals.email import (
    get_value_of_annual_rental_fee_awaiting_payment_confirmation,
    send_annual_rental_fee_invoice
)
from disturbance.components.approvals.serializers import ApprovalLogEntrySerializer
from disturbance.components.proposals.models import (
    Proposal, ApiarySiteFeeRemainder,
    ApiarySiteFeeType, SiteCategory,
    ProposalApiary
)
from disturbance.components.main.models import ApplicationType
from disturbance.components.organisations.models import Organisation
from disturbance.components.ap_payments.invoice_pdf import create_invoice_pdf_bytes
from disturbance.components.ap_payments.confirmation_pdf import create_confirmation_pdf_bytes
from disturbance.components.proposals.utils import proposal_submit_apiary
from disturbance.components.ap_payments.email import (
    send_application_fee_invoice_apiary_email_notification,
)
from disturbance.components.ap_payments.utils import (
    checkout,
    create_fee_lines,
    get_session_application_invoice,
    set_session_application_invoice,
    delete_session_application_invoice,
    get_session_site_transfer_application_invoice,
    set_session_site_transfer_application_invoice,
    delete_session_site_transfer_application_invoice, set_session_annual_rental_fee, get_session_annual_rental_fee,
    delete_session_annual_rental_fee, round_amount_according_to_env, checkout_existing_invoice, set_session_invoice,
    get_session_invoice, delete_session_invoice, InvoiceReferenceNotInSettionException,
)

from disturbance.components.ap_payments.models import ApplicationFee, ApplicationFeeInvoice, AnnualRentalFee
from ledger_api_client.utils import update_payments
from decimal import Decimal

from ledger_api_client.ledger_models import Invoice
from ledger_api_client.ledger_models import Basket
from ledger_api_client.order import Order
from disturbance.helpers import is_internal, is_in_organisation_contacts
from disturbance.context_processors import apiary_url

import logging
logger = logging.getLogger('apiary')


class AnnualRentalFeeView(TemplateView):
    def get_object(self):
        return get_object_or_404(AnnualRentalFee, id=self.kwargs['annual_rental_fee_id'])

    def restore_original_format(self, lines):
        for line in lines:
            for key in line:
                if key in ('price_incl_tax', 'price_excl_tax') and isinstance(line[key], (str, bytes)):  # Python 3 renamed the unicode type to str, the old str type has been replaced by bytes
                    amount_f = float(line[key])  # string to float
                    round_f = round_amount_according_to_env(amount_f)
                    decimal_f = Decimal(str(round_f))  # Generate Decimal with 2 decimal places string
                    line[key] = decimal_f
        return lines

    def get(self, request, *args, **kwargs):
        annual_rental_fee = self.get_object()

        try:
            with transaction.atomic():
                set_session_annual_rental_fee(request.session, annual_rental_fee)
                invoice = Invoice.objects.get(reference=annual_rental_fee.invoice_reference)

                proposal = annual_rental_fee.current_proposal

                lines, db_processes_after_success = create_fee_lines(proposal)
                request.session['db_processes'] = db_processes_after_success

                checkout_response = checkout(
                        request,
                        proposal,
                        lines,
                        return_url_ns='invoice_payment_success',
                        return_preload_url_ns='invoice_payment_success',
                        invoice_text=invoice.text,
                    )

                logger.info('{} built payment line item {} for Annual Site Fee and handing over to payment gateway'.format(
                    'User {} with id {}'.format(
                        request.user.get_full_name(), request.user.id
                    ), annual_rental_fee.approval.lodgement_number
                ))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating Annual Site Fee: {}'.format(e))
            raise


class InvoicePaymentView(TemplateView):

    def get_object(self):
        return get_object_or_404(Invoice, reference=self.kwargs['invoice_reference'])

    def post(self, request, *args, **kwargs):
        invoice = self.get_object()
        
        try:
            with transaction.atomic():

                proposal = Proposal.objects.get(lodgement_number=invoice.reference)
                lines, db_processes_after_success = create_fee_lines(proposal)

                set_session_invoice(request.session, invoice)
                request.session['db_processes'] = db_processes_after_success

                checkout_response = checkout(
                        request,
                        proposal,
                        lines,
                        return_url_ns='invoice_payment_success',
                        return_preload_url_ns='invoice_payment_success',
                        invoice_text=invoice.text,
                    )

                if request.user.id:
                    logger.info('{} handing over to payment gateway for the invoice: {}'.format(
                        'User {} with id {}'.format(request.user.get_full_name(), request.user.id),
                        invoice.reference
                    ))
                else:
                    logger.info('Anonymous user handing over to payment gateway for the invoice: {}'.format(invoice.reference))

                return checkout_response

        except Exception as e:
            logger.error('Error Creating Annual Site Fee: {}'.format(e))
            raise


class ApplicationFeeView(TemplateView):
    template_name = 'disturbance/payment/success_fee.html'

    def get_object(self):
        return get_object_or_404(Proposal, id=self.kwargs['proposal_pk'])

    def post(self, request, *args, **kwargs):

        proposal = self.get_object()
        application_fee = ApplicationFee.objects.create(proposal=proposal, created_by=request.user, payment_type=ApplicationFee.PAYMENT_TYPE_TEMPORARY)

        try:
            with transaction.atomic():
                if proposal.application_type.name == ApplicationType.SITE_TRANSFER:
                    set_session_site_transfer_application_invoice(request.session, application_fee)
                else:
                    set_session_application_invoice(request.session, application_fee)
                lines, db_processes_after_success = create_fee_lines(proposal)

                if proposal.application_type.name == ApplicationType.SITE_TRANSFER:
                    checkout_response = checkout(
                        request,
                        proposal,
                        lines,
                        return_url_ns='site_transfer_fee_success',
                        return_preload_url_ns='site_transfer_fee_success',
                        invoice_text='Site Transfer Application Fee'
                    )
                else:
                    request.session['db_processes'] = db_processes_after_success
                    checkout_response = checkout(
                        request,
                        proposal,
                        lines,
                        return_url_ns='fee_success',
                        return_preload_url_ns='fee_success',
                        invoice_text='Application Fee'
                    )

                logger.info('{} built payment line item {} for Application Fee and handing over to payment gateway'.format('User {} with id {}'.format(proposal.submitter.get_full_name(),proposal.submitter.id), proposal.id))
                return checkout_response

        except Exception as e:
            logger.error('Error Creating Application Fee: {}'.format(e))
            if application_fee:
                application_fee.delete()
            raise


class SiteTransferApplicationFeeSuccessView(TemplateView):
    template_name = 'disturbance/payment/success_fee.html'

    def get(self, request, *args, **kwargs):
        print (" SITE TRANSFER APPLICATION FEE SUCCESS ")
        #print(request.session.__dict__)

        proposal = None
        submitter = None
        invoice = None
        try:
            application_fee = get_session_site_transfer_application_invoice(request.session)
            proposal = application_fee.proposal
            try:
                if proposal.applicant:
                    recipient = proposal.applicant.email
                    #submitter = proposal.applicant
                elif proposal.proxy_applicant:
                    recipient = proposal.proxy_applicant.email
                    #submitter = proposal.proxy_applicant
                else:
                    recipient = proposal.submitter.email
                    #submitter = proposal.submitter
            except:
                recipient = proposal.submitter.email
            submitter = proposal.submitter

            if self.request.user.is_authenticated:
                basket = Basket.objects.filter(status='Submitted', owner=request.user).order_by('-id')[:1]
            else:
                basket = Basket.objects.filter(status='Submitted', owner=booking.proposal.submitter).order_by('-id')[:1]

            order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(order_number=order.number)
            invoice_ref = invoice.reference
            fee_inv, created = ApplicationFeeInvoice.objects.get_or_create(application_fee=application_fee, invoice_reference=invoice_ref)

            if application_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=inv.order_number)
                    #order.user = submitter
                    order.user = request.user
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error('{} tried paying an application fee with an incorrect invoice'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user'))
                    return redirect('external-proposal-detail', args=(proposal.id,))
                if inv.system not in ['0517']:
                    logger.error('{} tried paying an application fee with an invoice from another system with reference number {}'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user',inv.reference))
                    return redirect('external-proposal-detail', args=(proposal.id,))

                if fee_inv:
                    #application_fee.payment_type = 1  # internet booking
                    application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                    application_fee.expiry_time = None
                    update_payments(invoice_ref)

                    if proposal and (invoice.payment_status == 'paid' or invoice.payment_status == 'over_paid'):
                        # proposal.fee_invoice_reference = invoice_ref
                        if isinstance(proposal.fee_invoice_references, list):
                            proposal.fee_invoice_references.append(invoice_ref)
                        else:
                            proposal.fee_invoice_references = [invoice_ref,]
                        proposal.save()
                        proposal_submit_apiary(proposal, request)
                    else:
                        logger.error('Invoice payment status is {}'.format(invoice.payment_status))
                        raise

                    application_fee.save()
                    request.session['site_transfer_last_app_invoice'] = application_fee.id
                    delete_session_site_transfer_application_invoice(request.session)

                    send_application_fee_invoice_apiary_email_notification(request, proposal, invoice, recipients=[recipient])
                    #send_application_fee_confirmation_apiary_email_notification(request, application_fee, invoice, recipients=[recipient])

                    context = {
                        'proposal': proposal,
                        'submitter': submitter,
                        'fee_invoice': invoice
                    }
                    return render(request, self.template_name, context)

        except Exception as e:
            #import ipdb; ipdb.set_trace()
            if ('site_transfer_last_app_invoice' in request.session) and ApplicationFee.objects.filter(id=request.session['site_transfer_last_app_invoice']).exists():
                application_fee = ApplicationFee.objects.get(id=request.session['site_transfer_last_app_invoice'])
                proposal = application_fee.proposal
                try:
                    if proposal.applicant:
                        recipient = proposal.applicant.email
                        #submitter = proposal.applicant
                    elif proposal.proxy_applicant:
                        recipient = proposal.proxy_applicant.email
                        #submitter = proposal.proxy_applicant
                    else:
                        recipient = proposal.submitter.email
                        #submitter = proposal.submitter
                except:
                    recipient = proposal.submitter.email
                submitter = proposal.submitter

                if ApplicationFeeInvoice.objects.filter(application_fee=application_fee).count() > 0:
                    afi = ApplicationFeeInvoice.objects.filter(application_fee=application_fee)
                    invoice = afi[0]
            else:
                return redirect('home')
        context = {
            'proposal': proposal,
            'submitter': submitter,
            'fee_invoice': invoice
        }
        return render(request, self.template_name, context)


class InvoicePaymentSuccessView(TemplateView):
    template_name = 'disturbance/payment/invoice_payment_success.html'

    def get(self, request, *args, **kwargs):
        invoice = None

        try:
            invoice = get_session_invoice(request.session)  # When accessed 2nd time, this raises an Exception
            request.session['last_invoice_reference'] = invoice.reference
            delete_session_invoice(request.session)

            context = {}
            return render(request, self.template_name, context)

        except Invoice.DoesNotExist:
            logger.error('Invoice reference:{} not found in the database'.format(request.session['last_invoice_reference']))
            return redirect('home')

        except InvoiceReferenceNotInSettionException as e:
            if 'last_invoice_reference' in request.session and Invoice.objects.filter(reference=request.session['last_invoice_reference']).exists():
                invoice = Invoice.objects.get(reference=request.session['last_invoice_reference'])
                del request.session['last_invoice_reference']
                request.session.modified = True

                annual_rental_fee = AnnualRentalFee.objects.filter(invoice_reference=invoice.reference)
                application_fee_invoice = ApplicationFeeInvoice.objects.filter(invoice_reference=invoice.reference)
                if annual_rental_fee:
                    # This invoice is issued for the Annual Site Fee
                    annual_rental_fee = annual_rental_fee.first()
                    can_access_invoice, to_email_addresses = AnnualRentalFeeSuccessView.send_invoice_mail(annual_rental_fee, invoice, request)
                    self.template_name = 'disturbance/payment/annual_rental_fee_success.html'

                    context = {
                        'invoice_reference': invoice.reference,
                        'to_email_address': to_email_addresses,
                        'can_access_invoice': can_access_invoice,
                    }
                    return render(request, self.template_name, context)
                else:
                    # Should not reach here,
                    # At the moment, invoice for the annual rental fee is the only the invoice issued before actual payments
                    return redirect('home')
            else:
                return redirect('home')
        except Exception as e:
            logger.error('Error after payment success: {}'.format(e))
            return redirect('home')


class AnnualRentalFeeSuccessView(TemplateView):
    template_name = 'disturbance/payment/annual_rental_fee_success.html'

    def get(self, request, *args, **kwargs):
        invoice = None

        try:
            # When accessed first time, there is a annual_rental_fee in the session which was set at AnnualRentalFeeView()
            # but when accessed sencond time, it is deleted therefore raise an error.
            annual_rental_fee = get_session_annual_rental_fee(request.session)

            # if self.request.user.is_authenticated:
            #     basket = Basket.objects.filter(status='Submitted', owner=request.user).order_by('-id')[:1]
            # else:
            #     pass

            # order = Order.objects.get(basket=basket[0])
            invoice = Invoice.objects.get(reference=annual_rental_fee.invoice_reference)
            # annual_rental_fee.invoice_reference = invoice.reference
            # annual_rental_fee.save()

            request.session['last_annual_rental_fee_id'] = annual_rental_fee.id
            delete_session_annual_rental_fee(request.session)

            can_access_invoice, to_email_addresses = AnnualRentalFeeSuccessView.send_invoice_mail(annual_rental_fee, invoice, request)

            context = {
                'invoice_reference': annual_rental_fee.invoice_reference,
                'to_email_address': to_email_addresses,
                'can_access_invoice': can_access_invoice,
            }
            return render(request, self.template_name, context)

        except Exception as e:
            if 'last_annual_rental_fee_id' in request.session and AnnualRentalFee.objects.filter(id=request.session['last_annual_rental_fee_id']).exists():
                annual_rental_fee = AnnualRentalFee.objects.get(id=request.session['last_annual_rental_fee_id'])
                del request.session['last_annual_rental_fee_id']
                request.session.modified = True

                # TODO: Display success screen
                to_email_addresses = annual_rental_fee.approval.relevant_applicant.email
                can_access_invoice = False
                if request.user == annual_rental_fee.approval.relevant_applicant or \
                        annual_rental_fee.approval.applicant in request.user.disturbance_organisations.all():
                    can_access_invoice = True

                context = {
                    'invoice_reference': annual_rental_fee.invoice_reference,
                    'to_email_address': to_email_addresses,
                    'can_access_invoice': can_access_invoice,
                }
                return render(request, self.template_name, context)
            else:
                return redirect('home')

        except AnnualRentalFee.DoesNotExist:
            logger.error('AnnualRentalFee id:{} not found in the database'.format(request.session['last_annual_rental_fee_id']))
            return redirect('home')

    @staticmethod
    def send_invoice_mail(annual_rental_fee, invoice, request):
        # Send invoice
        to_email_addresses = annual_rental_fee.approval.relevant_applicant.email
        email_data = send_annual_rental_fee_invoice(annual_rental_fee.approval, invoice, [to_email_addresses, ])

        # Add comms log
        email_data['approval'] = u'{}'.format(annual_rental_fee.approval.id)
        serializer = ApprovalLogEntrySerializer(data=email_data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        # Check if the request.user can access the invoice
        can_access_invoice = False
        if not request.user.is_anonymous():
            if request.user == annual_rental_fee.approval.relevant_applicant or \
                    annual_rental_fee.approval.applicant in request.user.disturbance_organisations.all():
                can_access_invoice = True

        return can_access_invoice, to_email_addresses


class ApplicationFeeSuccessView(TemplateView):
    template_name = 'disturbance/payment/success_fee.html'

    def get(self, request, *args, **kwargs):
        proposal = None
        submitter = None
        invoice = None
        try:
            # Retrieve db processes stored when calculating the fee, and delete the session
            db_operations = request.session['db_processes']
            del request.session['db_processes']

            application_fee = get_session_application_invoice(request.session)
            proposal = application_fee.proposal
            try:
                if proposal.applicant:
                    recipient = proposal.applicant.email
                    #submitter = proposal.applicant
                elif proposal.proxy_applicant:
                    recipient = proposal.proxy_applicant.email
                    #submitter = proposal.proxy_applicant
                else:
                    recipient = proposal.submitter.email
                    #submitter = proposal.submitter
            except:
                recipient = proposal.submitter.email
            submitter = proposal.submitter

            invoice = Invoice.objects.filter(reference=proposal.lodgement_number).order_by('id').last()
            invoice_ref = invoice.reference
            fee_inv, created = ApplicationFeeInvoice.objects.get_or_create(application_fee=application_fee, invoice_reference=invoice_ref)

            if application_fee.payment_type == ApplicationFee.PAYMENT_TYPE_TEMPORARY:
                try:
                    inv = Invoice.objects.get(reference=invoice_ref)
                    order = Order.objects.get(number=inv.order_number)
                    #order.user = submitter
                    order.user = request.user
                    order.save()
                except Invoice.DoesNotExist:
                    logger.error('{} tried paying an application fee with an incorrect invoice'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user'))
                    return redirect('external-proposal-detail', args=(proposal.id,))
                if inv.system not in ['0517']:
                    logger.error('{} tried paying an application fee with an invoice from another system with reference number {}'.format('User {} with id {}'.format(proposal.submitter.get_full_name(), proposal.submitter.id) if proposal.submitter else 'An anonymous user',inv.reference))
                    return redirect('external-proposal-detail', args=(proposal.id,))

                if fee_inv:
                    #application_fee.payment_type = 1  # internet booking
                    application_fee.payment_type = ApplicationFee.PAYMENT_TYPE_INTERNET
                    application_fee.expiry_time = None
                    update_payments(invoice_ref)

                    if proposal and (invoice.payment_status == 'paid' or invoice.payment_status == 'over_paid'):
                        # proposal.fee_invoice_reference = invoice_ref
                        if isinstance(proposal.fee_invoice_references, list):
                            proposal.fee_invoice_references.append(invoice_ref)
                        else:
                            proposal.fee_invoice_references = [invoice_ref,]
                        proposal.save()
                        proposal_submit_apiary(proposal, request)
                        self.adjust_db_operations(db_operations)
                    else:
                        logger.error('Invoice payment status is {}'.format(invoice.payment_status))
                        raise

                    application_fee.save()
                    request.session['das_last_app_invoice'] = application_fee.id
                    delete_session_application_invoice(request.session)

                    send_application_fee_invoice_apiary_email_notification(request, proposal, invoice, recipients=[recipient])
                    #send_application_fee_confirmation_apiary_email_notification(request, application_fee, invoice, recipients=[recipient])
                    context = {
                        'proposal': proposal,
                        'submitter': submitter,
                        'fee_invoice': invoice
                    }
                    return render(request, self.template_name, context)

        except Exception as e:
            if ('das_last_app_invoice' in request.session) and ApplicationFee.objects.filter(id=request.session['das_last_app_invoice']).exists():
                application_fee = ApplicationFee.objects.get(id=request.session['das_last_app_invoice'])
                proposal = application_fee.proposal

                try:
                    if proposal.applicant:
                        recipient = proposal.applicant.email
                        #submitter = proposal.applicant
                    elif proposal.proxy_applicant:
                        recipient = proposal.proxy_applicant.email
                        #submitter = proposal.proxy_applicant
                    else:
                        recipient = proposal.submitter.email
                        #submitter = proposal.submitter
                except:
                    recipient = proposal.submitter.email
                submitter = proposal.submitter

                if ApplicationFeeInvoice.objects.filter(application_fee=application_fee).count() > 0:
                    afi = ApplicationFeeInvoice.objects.filter(application_fee=application_fee)
                    fee_invoice = afi[0]
            else:
                return redirect('home')

        context = {
            'proposal': proposal,
            'submitter': submitter,
            'fee_invoice': fee_invoice
        }
        return render(request, self.template_name, context)

    def adjust_db_operations(self, db_operations):
        proposal_apiary = ProposalApiary.objects.get(id=db_operations['proposal_apiary_id'])

        proposal_apiary.post_payment_success()
        # non vacant site
        # for site_id in db_operations['apiary_site_ids']:
        #     apiary_site = ApiarySite.objects.get(id=site_id)
        #     proposal_apiary.set_status(apiary_site, ApiarySiteOnProposal.SITE_STATUS_PENDING)

        # vacant site
        # for site_id in db_operations['vacant_apiary_site_ids']:
        #     apiary_site = ApiarySite.objects.get(id=site_id,)
        #     apiary_site.is_vacant = False
        #     apiary_site.save()
        #     proposal_apiary.set_status(apiary_site, ApiarySiteOnProposal.SITE_STATUS_PENDING)

        # Perform database operations to remove and/or store site remainders
        # site remainders used
        for item in db_operations['site_remainder_used']:
            site_remainder = ApiarySiteFeeRemainder.objects.get(id=item['id'])
            site_remainder.date_used = datetime.strptime(item['date_used'], '%Y-%m-%d')
            site_remainder.save()

        # site remainders added
        for item in db_operations['site_remainder_to_be_added']:
            apiary_site_fee_type = ApiarySiteFeeType.objects.get(name=item['apiary_site_fee_type_name'])
            site_category = SiteCategory.objects.get(id=item['site_category_id'])
            # date_expiry = datetime.strptime(item['date_expiry'], '%Y-%m-%d')
            applicant = Organisation.objects.get(id=item['applicant_id']) if item['applicant_id'] else None
            proxy_applicant = EmailUser.objects.get(id=item['proxy_applicant_id']) if item[
                'proxy_applicant_id'] else None

            site_remainder = ApiarySiteFeeRemainder.objects.create(
                site_category=site_category,
                apiary_site_fee_type=apiary_site_fee_type,
                applicant=applicant,
                proxy_applicant=proxy_applicant,
            )


class AwaitingPaymentPDFView(View):
    def get(self, request, *args, **kwargs):
        annual_rental_fee = get_object_or_404(AnnualRentalFee, id=self.kwargs['annual_rental_fee_id'])
        response = HttpResponse(content_type='application/pdf')
        response.write(get_value_of_annual_rental_fee_awaiting_payment_confirmation(annual_rental_fee))
        return response


class InvoicePDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, reference=self.kwargs['reference'])
        url_var = apiary_url(request)

        try:
            # Assume the invoice has been issued for the application(proposal)
            # proposal = Proposal.objects.get(fee_invoice_reference=invoice.reference)
            proposal = Proposal.objects.get(fee_invoice_references__contains=[invoice.reference])

            if proposal.relevant_applicant_type == 'organisation':
                organisation = proposal.applicant.organisation.organisation_set.all()[0]
                if self.check_owner(organisation):
                    response = HttpResponse(content_type='application/pdf')
                    response.write(create_invoice_pdf_bytes('invoice.pdf', invoice, url_var, proposal))
                    return response
                raise PermissionDenied
            else:
                response = HttpResponse(content_type='application/pdf')
                response.write(create_invoice_pdf_bytes('invoice.pdf', invoice, url_var, proposal))
                return response
        except Proposal.DoesNotExist:
            # The invoice might be issued for the annual site fee
            annual_rental_fee = AnnualRentalFee.objects.get(invoice_reference=invoice.reference)
            approval = annual_rental_fee.approval
            response = HttpResponse(content_type='application/pdf')
            response.write(create_invoice_pdf_bytes('invoice.pdf', invoice, url_var, None))
            return response
        except:
            raise

    def get_object(self):
        return get_object_or_404(Invoice, reference=self.kwargs['reference'])

    def check_owner(self, organisation):
        return is_in_organisation_contacts(self.request, organisation) or is_internal(self.request) or self.request.user.is_superuser


class ConfirmationPDFView(View):
    def get(self, request, *args, **kwargs):
        invoice = get_object_or_404(Invoice, reference=self.kwargs['reference'])
        # proposal = Proposal.objects.get(fee_invoice_reference=invoice.reference)
        proposal = Proposal.objects.get(fee_invoice_references__contains=[invoice.reference])
        application_fee = proposal.application_fees.last()

        organisation = proposal.applicant.organisation.organisation_set.all()[0]
        if self.check_owner(organisation):
            response = HttpResponse(content_type='application/pdf')
            #import ipdb; ipdb.set_trace()
            response.write(create_confirmation_pdf_bytes('confirmation.pdf',invoice, application_fee))
            return response
        raise PermissionDenied

    def get_object(self):
        return  get_object_or_404(Invoice, reference=self.kwargs['reference'])

    def check_owner(self, organisation):
        return is_in_organisation_contacts(self.request, organisation) or is_internal(self.request) or self.request.user.is_superuser
