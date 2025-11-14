import datetime
from decimal import Decimal

import pytz
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from django.db import transaction
from django.db.models import Q, Min
#from ledger.checkout.utils import createCustomBasket
from ledger_api_client.ledger_models import Invoice
#from ledger.payments.invoice.utils import CreateInvoiceBasket
#from ledger.settings_base import TIME_ZONE
from ledger_api_client.utils import create_basket_session, process_create_future_invoice

from disturbance.components.approvals.email import send_annual_rental_fee_awaiting_payment_confirmation
from disturbance.components.approvals.models import Approval, ApiarySiteOnApproval
from disturbance.components.approvals.serializers import ApprovalLogEntrySerializer
from disturbance.components.ap_payments.models import AnnualRentalFee, AnnualRentalFeePeriod, AnnualRentalFeeApiarySite
from disturbance.components.ap_payments.utils import generate_line_items_for_annual_rental_fee
from disturbance.components.proposals.models import ApiaryAnnualRentalFeeRunDate, ApiaryAnnualRentalFeePeriodStartDate, \
    ApiarySite
from disturbance.settings import SITE_STATUS_CURRENT, SITE_STATUS_SUSPENDED, PAYMENT_SYSTEM_ID, PAYMENT_SYSTEM_PREFIX, APIARY_EXTERNAL_URL, TIME_ZONE

from collections import namedtuple
from django.urls import reverse
import uuid

import logging
logger = logging.getLogger(__name__)


def get_annual_rental_fee_period(target_date):
    """
    Retrieve the annual site fee period, the invoice for this period should have been issued on the target_date passed as a parameter
    """
    target_date_year = target_date.year

    # Calculate cron job period
    run_date = ApiaryAnnualRentalFeeRunDate.objects.get(name=ApiaryAnnualRentalFeeRunDate.NAME_CRON)
    run_date_month = run_date.date_run_cron.month
    run_date_day = run_date.date_run_cron.day

    # Calculate the run_date in the year where the target_date is in
    prev_run_date = datetime.date(year=target_date_year, month=run_date_month, day=run_date_day)
    if target_date < prev_run_date:
        # prev_run_date calculated above is in the future.  Calculate one before that
        prev_run_date = datetime.date(year=prev_run_date.year-1, month=prev_run_date.month, day=prev_run_date.day)

    # Calculate annual site fee period
    # annual site fee start date must be between the prev_run_date and next_run_date
    start_date = ApiaryAnnualRentalFeePeriodStartDate.objects.get(name=ApiaryAnnualRentalFeePeriodStartDate.NAME_PERIOD_START)
    period_start_date_month = start_date.period_start_date.month
    period_start_date_day = start_date.period_start_date.day

    # Calculate the period start date in the year where the prev_run_date is in
    period_start_date = datetime.date(year=prev_run_date.year, month=period_start_date_month, day=period_start_date_day)
    if period_start_date < prev_run_date:
        # period_start_date calculated above is before the previous cron job run date.  Calculate the next one
        period_start_date = datetime.date(year=period_start_date.year+1, month=period_start_date.month, day=period_start_date.day)

    period_end_date = datetime.date(year=period_start_date.year+1, month=period_start_date.month, day=period_start_date.day) - datetime.timedelta(days=1)

    return period_start_date, period_end_date


def get_approvals(annual_rental_fee_period):
    # Retrieve the licences which will be valid within this period and no invoices have been issued for this period
    q_objects = Q()
    q_objects &= Q(apiary_approval=True)
    q_objects &= Q(expiry_date__gte=annual_rental_fee_period.period_start_date)
    q_objects &= Q(status__in=[Approval.STATUS_CURRENT, Approval.STATUS_SUSPENDED])

    approval_qs = Approval.objects.filter(q_objects).exclude(
        # We don't want to send an invoice for the same period
        annual_rental_fees__in=AnnualRentalFee.objects.filter(annual_rental_fee_period=annual_rental_fee_period)
    )

    return approval_qs


# def get_apiary_sites_to_be_charged(approval, annual_rental_fee_period):
#     apiary_sites = ApiarySite.objects.filter(
#         id__in=(ApiarySiteOnApproval.objects.filter(approval=approval, site_status__in=(SITE_STATUS_CURRENT, SITE_STATUS_SUSPENDED,)).values_list('apiary_site_id', flat=True))
#     )
#     return apiary_sites

    # 1. Retrieve all the annual_rental_fees under this approval and this annual_rental_fee_period
    #       annual_rental_fees = AnnualRentalFee.objects.filter(approval=approval, annual_rental_fee_period=annual_rental_fee_period)
    # 2. Retrieve all the current and suspended apiary_sites under this approval
    #       sites_status_current = approval.apiary_sites.filter(status=ApiarySite.STATUS_CURRENT)
    # 3. Retrieve apiary_sites which invoices have been issued for already
    #       annual_rental_fee_apiary_sites = AnnualRentalFeeApiarySite.objects.filter(apiary_site__in=sites_status_current, annual_rental_fee__in=annual_rental_fees)
    #       sites_exclude = ApiarySite.objects.filter(annualrentalfeeapiarysite__in=annual_rental_fee_apiary_sites)

    # Combine the queries above
#    apiary_sites = ApiarySite.objects.filter(
#        id__in=(ApiarySiteOnApproval.objects.filter(approval=approval, site_status__in=(SITE_STATUS_CURRENT, SITE_STATUS_SUSPENDED,)).values_list('apiary_site_id', flat=True))
#    ).exclude(
#        # Exclude the apiaries for which the invoices have been issued for this period
#        annualrentalfeeapiarysite__in=AnnualRentalFeeApiarySite.objects.filter(
#            annual_rental_fee__in=AnnualRentalFee.objects.filter(
#                approval=approval,
#                # annual_rental_fee_period=annual_rental_fee_period
#                invoice_period_end_date__gte=annual_rental_fee_period.period_end_date
#            )
#        )
#    )
#    return apiary_sites


class Command(BaseCommand):
    help = 'Send annual rent fee invoices for the apiary'

    def handle(self, *args, **options):
        try:
            run_date = ApiaryAnnualRentalFeeRunDate.objects.get(name=ApiaryAnnualRentalFeeRunDate.NAME_CRON)
            if not run_date.enabled:
                # Cron is disabled.  Do nothing
                return

            # Determine the start and end date of the annual site fee, for which the invoices should be issued
            today_now_local = datetime.datetime.now(pytz.timezone(TIME_ZONE))
            today_date_local = today_now_local.date()
            period_start_date, period_end_date = get_annual_rental_fee_period(today_date_local)

            # Retrieve annual site fee period object for the period calculated above
            # This period should not overwrap the existings, otherwise you will need a refund
            annual_rental_fee_period, created = AnnualRentalFeePeriod.objects.get_or_create(period_start_date=period_start_date, period_end_date=period_end_date)

            # Retrieve the licences which will be valid within the current annual site fee period
            approval_qs = get_approvals(annual_rental_fee_period)

            # Issue the annual site fee invoices per approval per annual_rental_fee_period
            errors = []
            updates = []
            for approval in approval_qs:
                try:
                    with transaction.atomic():
                        # apiary_sites_to_be_charged = get_apiary_sites_to_be_charged(approval, annual_rental_fee_period)
                        apiary_sites_to_be_charged = ApiarySite.objects.filter(
                            id__in=(ApiarySiteOnApproval.objects.filter(approval=approval, site_status__in=(
                                SITE_STATUS_CURRENT, SITE_STATUS_SUSPENDED,)).values_list('apiary_site_id', flat=True))
                        )

                        if apiary_sites_to_be_charged.count() > 0:
                            # invoice, details_dict = create_other_invoice_for_annual_rental_fee(approval, today_now_local, (period_start_date, period_end_date), apiary_sites_to_be_charged)
                            line_items, apiary_sites_charged, invoice_period = generate_line_items_for_annual_rental_fee(
                                approval,
                                today_now_local,
                                (annual_rental_fee_period.period_start_date, annual_rental_fee_period.period_end_date),
                                apiary_sites_to_be_charged
                            )

                            if line_items:
                                with transaction.atomic():
                                    try:
                                        logger.info('Creating annual site fee invoice for the approval {}'.format(approval.lodgement_number))

                                        # basket = createCustomBasket(line_items, approval.relevant_applicant_email_user, PAYMENT_SYSTEM_ID)
                                        # order = CreateInvoiceBasket(
                                        #     payment_method='other', system=PAYMENT_SYSTEM_PREFIX
                                        # ).create_invoice_and_order(basket, 0, None, None, user=approval.relevant_applicant_email_user,
                                        #                            invoice_text='Payment Invoice')
                                        # invoice = Invoice.objects.get(order_number=order.number)
                                        MockRequest = namedtuple("MockRequest", ["user"])
                                        request = MockRequest(user=approval.relevant_applicant_email_user)
                                        invoice_uuid = uuid.uuid4()

                                        basket_params = {
                                            'products': line_items,
                                            'vouchers': [],
                                            'system': PAYMENT_SYSTEM_ID,
                                            'custom_basket': True,
                                            'booking_reference': approval.lodgement_number,
                                            'booking_reference_link': approval.lodgement_number,
                                            'no_payment': False,
                                        }
                                        basket_hash = create_basket_session(request, approval.relevant_applicant_email_user.id, basket_params)
                                        basket_hash = basket_hash.split("|")[0]
                                        invoice_text='Payment Invoice'
                                        return_preload_url = APIARY_EXTERNAL_URL + reverse("ledger-api-success-callback", kwargs={"uuid": application_fee.uuid})
                                        
                                        future_invoice = process_create_future_invoice(
                                            basket_hash, invoice_text, return_preload_url
                                        )
                                        data = future_invoice["data"]
                                        invoice_reference = data["invoice"]
                                        
                                        line_items = make_serializable(
                                            line_items)  # Make line items serializable to store in the JSONField
                                        annual_rental_fee = AnnualRentalFee.objects.create(
                                            approval=approval,
                                            annual_rental_fee_period=annual_rental_fee_period,
                                            invoice_reference=invoice_reference,
                                            invoice_period_start_date=invoice_period[0],
                                            invoice_period_end_date=invoice_period[1],
                                            lines=line_items,
                                        )

                                        updates.append(annual_rental_fee.invoice_reference)
                                    except Exception as e:
                                        err_msg = 'Failed to create annual site fee confirmation'
                                        logger.error('{}\n{}'.format(err_msg, str(e)))
                                        errors.append(err_msg)

                                # Store the apiary sites which the invoice created above has been issued for
                                for apiary_site in apiary_sites_to_be_charged:
                                    annual_rental_fee_apiary_site = AnnualRentalFeeApiarySite(apiary_site=apiary_site, annual_rental_fee=annual_rental_fee)
                                    annual_rental_fee_apiary_site.save()

                                # Update invoice_sent attribute of the annual_rental_fee obj?
                                email_data = send_annual_rental_fee_awaiting_payment_confirmation(approval, annual_rental_fee, invoice)

                                email_data['approval'] = u'{}'.format(approval.id)
                                serializer = ApprovalLogEntrySerializer(data=email_data)
                                serializer.is_valid(raise_exception=True)
                                serializer.save()

                except Exception as e:
                    err_msg = 'Failed to send an annual site fee invoice for the approval {}'.format(approval.lodgement_number)
                    logger.error('{}\n{}'.format(err_msg, str(e)))
                    errors.append(err_msg)

        except Exception as e:
            err_msg = 'Error command {}'.format(__name__)
            logger.error('{}\n{}'.format(err_msg, str(e)))
            errors.append(err_msg)

        cmd_name = __name__.split('.')[-1].replace('_', ' ').upper()
        err_str = '<strong style="color: red;">Errors: {}</strong>'.format(len(errors)) if len(errors)>0 else '<strong style="color: green;">Errors: 0</strong>'
        msg = '<p>{} completed. {}. IDs updated: {}.</p>'.format(cmd_name, err_str, updates)
        logger.info(msg)
        print(msg) # will redirect to cron_tasks.log file, by the parent script


def make_serializable(line_items):
    for line in line_items:
        for key in line:
            if isinstance(line[key], Decimal):
                # Convert Decimal to str
                line[key] = str(line[key])
    return line_items
