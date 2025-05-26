from ledger_api_client.ledger_models import Invoice
from rest_framework import serializers

from disturbance.components.ap_payments.models import AnnualRentalFee, AnnualRentalFeePeriod


class AnnualRentalFeePeriodSerializer(serializers.ModelSerializer):
    year_name = serializers.SerializerMethodField()

    class Meta:
        model = AnnualRentalFeePeriod
        fields = (
            'id',
            'period_start_date',
            'period_end_date',
            'year_name',
        )

    def get_year_name(self, obj):
        return str(obj.period_start_date.year) + ' (' + obj.period_start_date.strftime('%d/%m/%Y') + ' to ' + obj.period_end_date.strftime('%d/%m/%Y') + ')'


class AnnualRentalFeeSerializer(serializers.ModelSerializer):
    annual_rental_fee_invoice_url = serializers.SerializerMethodField()
    annual_rental_fee_period = AnnualRentalFeePeriodSerializer()
    payment_status = serializers.SerializerMethodField()

    class Meta:
        model = AnnualRentalFee
        fields = (
            'id',
            'annual_rental_fee_period',
            'invoice_period_start_date',
            'invoice_period_end_date',
            'invoice_reference',
            'annual_rental_fee_invoice_url',
            'payment_status',
        )

    def validate(self, attr):
        return attr

    def get_annual_rental_fee_invoice_url(self, obj):
        return '/payments/invoice-pdf/{}'.format(obj.invoice_reference) if obj.invoice_reference else None

    def get_payment_status(self, obj):
        try:
            invoice = Invoice.objects.get(reference=obj.invoice_reference)
            return invoice.payment_status
        except Invoice.DoesNotExist:
            if obj.lines and obj.lines[0]:  # The default value of the JSONField is [''], that's why we have to check if lines[0] is not empty
                return 'unpaid'
            else:
                raise

