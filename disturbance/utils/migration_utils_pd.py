from ledger.accounts.models import Organisation as ledger_organisation
from ledger.accounts.models import OrganisationAddress
from ledger_api_client.ledger_models import EmailUserRO as EmailUser
from ledger_api_client.ledger_models import Invoice
from django.conf import settings
from disturbance.components.organisations.models import Organisation, OrganisationContact, UserDelegation
from disturbance.components.main.models import ApplicationType
from disturbance.components.main.utils import get_category
from disturbance.components.proposals.models import Proposal, ProposalType, ApiarySite, ApiarySiteOnProposal, ProposalApiary #, ProposalOtherDetails, ProposalPark
from disturbance.components.approvals.models import Approval, MigratedApiaryLicence, ApiarySiteOnApproval
#from commercialoperator.components.bookings.models import ApplicationFee, ParkBooking, Booking
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError, transaction
from django.contrib.gis.geos import GEOSGeometry
from django.utils import timezone
from ledger.address.models import Country
import csv
import os
import datetime
import time
import string
import pandas as pd
import numpy as np

from dateutil.relativedelta import relativedelta
from decimal import Decimal

import logging
logger = logging.getLogger(__name__)

NL = '\n'

COLUMN_MAPPING = {
    'Permit No':              'permit_number',
    'Start Date':             'start_date',
    'Expiry Date':            'expiry_date',
    'Issue Date':             'issue_date',
    'Status':                 'status',
    'Latitude':               'longitude', # these trwo reversed - incorect in spreadsheet
    'Longitude':              'latitude',  # these trwo reversed - incorect in spreadsheet
    'Trading Name':           'trading_name',
    'Licensee':               'licencee',
    'ABN':                    'abn',
    'First Name':             'first_name',
    'Surname':                'last_name',
    'Other Contact':          'other_contact',
    'Address 1':              'address_line1',
    'Address 2':              'address_line2',
    'Address 3':              'address_line3',
    'Suburb':                 'suburb',
    'State':                  'state',
    'Country':                'country',
    'Post':                   'postcode',
    'Telephone1':             'phone_number1',
    'Telephone2':             'phone_number2',
    'Mobile':                 'mobile_number',
    'EMAIL':                  'email',
    'licensed_site':          'licensed_site',
    'batch_no':               'batch_no',
    'approval_cpc_date':      'approval_cpc_date',
    'approval_minister_date': 'approval_minister_date',
    'map_ref':                'map_ref',
    'forest_block':           'forest_block',
    'cog':                    'cog',
    'roadtrack':              'roadtrack',
    'zone':                   'zone',
    'catchment':              'catchment',
    'dra_permit':             'dra_permit',
    'suspended':              'site_status',
}


class ApiaryLicenceReader():
    """
    FROM shell_plus:
        from disturbance.utils.migration_utils_pd import ApiaryLicenceReader
        alr = ApiaryLicenceReader('disturbance/utils/csv/apiary_migration_file_02Jun2022.xlsx')

        alr.create_users()

        alr.create_organisations()

        approvals_created = alr.create_licences()
        (All the approvals created are returned as a list)

        alr.create_licence_pdf(approvals_created)
        (Pass approvals as a list or a queryset)

    FROM mgt-command:
        python manage_ap.py apiary_migration_script --filename disturbance/utils/csv/apiary_migration_file_02Jun2022.xlsx


    Check for unique permit numbers
        pm = df['permit_number'].value_counts().loc[lambda x: x>1][1:].astype('int')
        pm.to_excel('/tmp/permit_numbers.xlsx')

    """

    def __init__(self, filename):
        self.df = self._read_excel(filename)
        self.application_type = ApplicationType.objects.get(name=ApplicationType.APIARY)
        self.proposal_type = ProposalType.objects.all().order_by('name', '-version').distinct('name').get(name=self.application_type.name)

    def __get_phone_number(self, row):
        try: 
            return row.phone_number1 
        except: 
            return row.mobile_number

    def __get_mobile_number(self, row):
        try: 
            return row.mobile_number 
        except: 
            return row.phone_number1

    def _read_excel(self, filename):
        def _get_country_code(x):
            try:
                country=Country.objects.get(iso_3166_1_a2=x.get('country'))
            except Exception as e:
                country=Country.objects.get(iso_3166_1_a2='AU')
            return country.code


        df = pd.read_excel(filename)

        # Rename the cols from Spreadsheet headers to Model fields names
        df = df.rename(columns=COLUMN_MAPPING)
        df[df.columns] = df.apply(lambda x: x.str.strip() if isinstance(x, str) else x)
        df['start_date']             = pd.to_datetime(df['start_date'], errors='coerce')
        df['expiry_date']            = pd.to_datetime(df['expiry_date'], errors='coerce')
        df['issue_date']             = pd.to_datetime(df['issue_date'], errors='coerce')
        df['approval_cpc_date']      = pd.to_datetime(df['approval_cpc_date'], errors='coerce')
        df['approval_minister_date'] = pd.to_datetime(df['approval_minister_date'], errors='coerce')

        df['issue_date'] = df.apply(lambda row: row.issue_date if isinstance(row.issue_date, datetime.datetime) else row.start_date, axis=1)
        df['abn']        = df['abn'].astype(str).str.replace(" ","").str.strip()
        df['email']      = df['email'].str.replace(" ","").str.lower().str.strip()
        #df['abn']        = df['abn'].str.strip().str.lower()
        #df['email']      = df['email'].str.strip().str.lower()
        df['first_name'] = df['first_name'].apply(lambda x: x.lower().capitalize().strip() if not pd.isnull(x) else 'No First Name')
        df['last_name']  = df['last_name'].apply(lambda x: x.lower().capitalize().strip() if not pd.isnull(x) else 'No Last Name')
        df['licencee']   = df['licencee'].apply(lambda x: x.strip() if not pd.isnull(x) else 'No Licencee Name')
        df['postcode']   = df['postcode'].apply(lambda x: '0000' if pd.isnull(x) else x)
        #df['site_status']= df['site_status'].apply(lambda x: settings.SITE_STATUS_SUSPENDED if not pd.isnull(x) else settings.SITE_STATUS_CURRENT)
        #df['dra_permit'] = df['site_status'].apply(lambda x: True if not pd.isnull(x) else False)
        df['country']    = df['country'].apply(_get_country_code)
 
        # clean everything else
        df.fillna('', inplace=True)
        df.replace({np.NaN: ''}, inplace=True)

        # check excel column names are the same column_mappings
        #import ipdb; ipdb.set_trace()
        if df.columns.values.tolist() != [*COLUMN_MAPPING.values()]:
            raise Exception('Column Names have changed!')

        # add extra column
        df['licencee_type'] = df['abn'].apply(lambda x: 'organisation' if x else 'individual')

        #import ipdb; ipdb.set_trace()
        #return df[:500]
        return df

    def run_migration(self):

        # create the users and organisations, if they don't already exist
        # t0_start = time.time()
        #try:
        self.create_users()
        self.create_organisations()
        #except Exception as e:
         #   print(e)
          #  import ipdb; ipdb.set_trace()
        # t0_end = time.time()
        # print('TIME TAKEN (Orgs and Users): {}'.format(t0_end - t0_start))

        # create the Migratiom models
        # t1_start = time.time()
        #try:
        approvals_affected = self.create_licences()
        #except Exception as e:
         #   print(e)
          #  import ipdb; ipdb.set_trace()
        # t1_end = time.time()
        # print('TIME TAKEN (Create License Models): {}'.format(t1_end - t1_start))

        # create the Licence/Permit PDFs
        # t2_start = time.time()
        try:
            self.create_licence_pdf(approvals_affected)
        except Exception as e:
            print(e)
            # import ipdb; ipdb.set_trace()
        # t2_end = time.time()
        # print('TIME TAKEN (Create License PDFs): {}'.format(t2_end - t2_start))

        # print('TIME TAKEN (Total): {}'.format(t2_end - t0_start))

    def create_users(self):
        # Iterate through the dataframe and create non-existent users
        for index, row in self.df.groupby('email').first().iterrows():
            #if row.status != 'Vacant':
            try:
                #    import ipdb; ipdb.set_trace()
                #first_name = data['first_name'] if not pd.isnull(data['first_name']) else 'No First Name'
                #last_name = data['last_name'] if not pd.isnull(data['last_name']) else 'No Last Name'
                #email = df['email']
                if not row.name:
                    continue
                user = EmailUser.objects.filter(email=row.name)
                if user.count() == 0:
                    user = EmailUser.objects.create(
                        email=row.name,
                        first_name=row.first_name,
                        last_name=row.last_name,
                        phone_number=self.__get_phone_number(row),
                        mobile_number=self.__get_mobile_number(row)
                    )
                    print('EmailUser: {} has been created.'.format(user.email))
            except Exception as e:
                # import ipdb; ipdb.set_trace()
                logger.error(f'user: {row.name}   *********** 1 *********** FAILED. {e}')

    def create_organisations(self):
        #import ipdb; ipdb.set_trace()
        count = 0
        for index, row in self.df.groupby('abn').first().iterrows():
            #import ipdb; ipdb.set_trace()
            #if count == 87:
            #    import ipdb; ipdb.set_trace()

            #if row.status != 'Vacant':
            if not row.name:
                continue
            try: 
                lo = ledger_organisation.objects.filter(abn=row.name)
            except Exception as e:
                # import ipdb; ipdb.set_trace()
                logger.error('{}'.format(e))
            try:

                if ledger_organisation.objects.filter(name=row.licencee).count() > 0:
                    licencee = row.licencee + ' (2)'

                if lo.count() > 0:
                    lo = lo[0]
                    org = lo.organisation_set.all()[0]
                    contact_qs = org.contacts.exclude(email__icontains='ledger.dpaw.wa.gov.au')

                    if not lo.postal_address:
                        # check org has a postal address
                        oa = self._create_org_address(row)
                        lo.postal_address = oa
                        lo.save()

                    if row.email and org.contacts.filter(email__icontains=row.email).count()==0:
                        # create contact
                        org_contact = self._create_org_contact(row, org)

                    if row.email and org.delegates.all().count()==0:
                        # create delegate
                        user = EmailUser.objects.get(email=row.email)
                        delegate = UserDelegation.objects.get_or_create(organisation=org, user=user)

                else:
                    oa = self._create_org_address(row)
                    lo = ledger_organisation.objects.create(
                        abn=row.name,
                        name=row.licencee,
                        postal_address=oa,
                        billing_address=oa,
                        trading_name=row.trading_name,
                    )
                    print('Organisation: {} has been created'.format(lo.abn))
                    org, created_org = Organisation.objects.get_or_create(organisation=lo)
                    org_contact = self._create_org_contact(row, org)
                    user = EmailUser.objects.get(email=row.email)
                    delegate = UserDelegation.objects.get_or_create(organisation=org, user=user)
            except Exception as e:
                # import ipdb; ipdb.set_trace()
                print(e)
                logger.error('{}'.format(e))
            count += 1
        print("Count: orgs: ".format(str(count)))

    def _create_org_address(self, row):
        oa = None
        try:
            oa, created = OrganisationAddress.objects.get_or_create(
                line1=row.address_line1,
                locality=row.suburb,
                postcode=str(int(row.postcode)),
                defaults={
                    'line2': row.address_line2,
                    'line3': row.address_line3,
                    'state': row.state,
                    'country': row.country,
                }
            )
        except MultipleObjectsReturned:
                oa = OrganisationAddress.objects.filter(
                    line1=row.address_line1,
                    locality=row.suburb,
                    postcode=str(int(row.postcode)),
                    line2=row.address_line2,
                    line3=row.address_line3,
                    state=row.state,
                    country=row.country
                ).first()
        except Exception as e:
            print(e)
            # import ipdb; ipdb.set_trace()
            logger.error('{}'.format(e))

        return oa

    def _create_org_contact(self, row, org):
        try:
            oc, created = OrganisationContact.objects.get_or_create(
                organisation=org,
                email=row.email,
                defaults={
                    'first_name': row.first_name,
                    'last_name': row.last_name,
                    'phone_number': self.__get_phone_number(row),
                    'mobile_number': self.__get_mobile_number(row),
                    'user_status': 'active',
                    'user_role': 'organisation_admin',
                    'is_admin': True
                }
            )

            if oc and not created:
                oc.user_role ='organisation_admin'
                oc.is_admin = True
                oc.user_status ='active'
                oc.save()

        except Exception as e:
            print('Org Contact: {}'.format(row))
            print(e)
            # import ipdb; ipdb.set_trace()
            logger.error('{}'.format(e))

    def create_licences(self):
        count = 1
        completed_site_numbers = []
        duplicate_site_numbers = []
        # skipped_indices = []
        approvals_affected = []

        with transaction.atomic():
            #for index, row in self.df[3244:].iterrows():
            for index, row in self.df.iterrows():
                try:
                    # TODO: remove once migration file has been corrected
                    # temp solution for vacant sites causing error
                    #if index in [3823, 6517]:
                     #   continue
                    site_number = None
                    # TODO: remove once migration file has been corrected
                    #if not row.permit_number and not row.licensed_site:
                    #    skipped_indices.append(index)
                    #    continue
                    #    raise ValueError("index: {} has no permit_number or licenced_site".format(index))
                    site_number = int(row.permit_number) if row.permit_number else int(row.licensed_site)
                    #ApiarySite.objects.filter(id=site_number)
                    if site_number not in completed_site_numbers and not ApiarySite.objects.filter(id=site_number).exists():

                        #if row.status != 'Vacant' and index>4474:
                        #if row.status != 'Vacant':
                            #import ipdb; ipdb.set_trace()
                        approval_affected = None
                        if row.licencee_type == 'organisation':
                            org = Organisation.objects.get(organisation__abn=row.abn)
                            user = EmailUser.objects.get(email=row.email)
                            approval_affected = self._migrate_approval(data=row, submitter=user, applicant=org, proxy_applicant=None)
                            # if created_approval:
                            #     approvals_created.append(created_approval)
                            # print("Permit No/licensed_site: {} migrated".format(site_number))

                        elif row.licencee_type == 'individual':
                            user = EmailUser.objects.get(email=row.email)
                            approval_affected = self._migrate_approval(data=row, submitter=user, applicant=None, proxy_applicant=user)

                        # else:
                            # declined and not to be reissued
                            # status = data['status']
                            # status = row.status

                        if approval_affected and approval_affected not in approvals_affected:
                            approvals_affected.append(approval_affected)

                        print("Permit No/licensed_site: {} migrated".format(site_number))

                        completed_site_numbers.append(site_number)
                        count += 1

                        print()
                        print(f'******************************************************** INDEX: {index}')
                        print()
                    else:
                        duplicate_site_numbers.append(site_number)

                except ValueError as e:
                    print(f'ERROR: SITE NUMBER {site_number} - SKIPPING')
                    # import ipdb; ipdb.set_trace()
                    raise e
                except Exception as e:
                    print(e)
                    # import ipdb; ipdb.set_trace()
                    raise e

        print(f'Duplicate Site Numbers: {duplicate_site_numbers}')
        # print('Skipped indices: {}'.format(skipped_indices))

        return approvals_affected

    def _migrate_approval(self, data, submitter, applicant=None, proxy_applicant=None):
        # created_approval = None
        approval_affected = None
        approval_created = False
        from disturbance.components.approvals.models import Approval
        #import ipdb; ipdb.set_trace()
        try:
            site_number = int(data.permit_number) if data.permit_number else int(data.licensed_site)
        except Exception as e:
            # import ipdb; ipdb.set_trace()
            print('ERROR: There is no site_number - Must provide a site number in migration spreadsheeet. {e}')

        try:
            expiry_date = data['expiry_date'] if data['expiry_date'] else datetime.date.today()
            start_date = data['start_date'] if data['start_date'] else datetime.date.today()
            issue_date = data['issue_date'] if data['issue_date'] else start_date
            site_status = 'not_to_be_reissued' if data['status'].lower().strip() == 'not to be reissued' else data['status'].lower().strip()

        except Exception as e:
            # import ipdb; ipdb.set_trace()
            print(e)

        try:

            #import ipdb; ipdb.set_trace()
            if applicant:
                proposal, p_created = Proposal.objects.get_or_create(
                                application_type=self.application_type,
                                activity='Apiary',
                                submitter=submitter,
                                applicant=applicant,
                                schema=self.proposal_type.schema,
                            )
                approval, approval_created = Approval.objects.update_or_create(
                                applicant=applicant,
                                status=Approval.STATUS_CURRENT,
                                apiary_approval=True,
                                defaults = {
                                    'issue_date':issue_date,
                                    'expiry_date':expiry_date,
                                    'start_date':start_date,
                                    #'submitter':submitter,
                                    'current_proposal':proposal,
                                    }
                            )
                approval_affected = approval
                if approval_created:
                    print('Approval: {} created'.format(approval))
            else:
                # import ipdb; ipdb.set_trace()
                pass

            #if 'PM' not in proposal.lodgement_number:
            #    proposal.lodgement_number = proposal.lodgement_number.replace('P', 'PM') # Application Migrated
            proposal.approval= approval
            proposal.processing_status='approved'
            proposal.customer_status='approved'
            proposal.migrated=True
            proposal.proposed_issuance_approval = {
                    'start_date': start_date.strftime('%d-%m-%Y'),
                    'expiry_date': expiry_date.strftime('%d-%m-%Y'),
                    'details': 'Migrated',
                    'cc_email': 'Migrated',
            }

            approval.migrated=True

            # create invoice for payment of zero dollars
            order = create_invoice(proposal)
            invoice = Invoice.objects.get(order_number=order.number) 
            proposal.fee_invoice_references = [invoice.reference]

            proposal.save()
            approval.save()

            # create apiary sites and intermediate table entries
            #geometry = GEOSGeometry('POINT(' + str(data['latitude']) + ' ' + str(data['longitude']) + ')', srid=4326)
            geometry = GEOSGeometry('POINT(' + str(data['latitude']) + ' ' + str(data['longitude']) + ')', srid=4326)
            #import ipdb; ipdb.set_trace()
            apiary_site = ApiarySite.objects.create(
                    id=site_number,
                    is_vacant=True if site_status=='vacant' else False
                    )
            site_category = get_category(geometry)
            intermediary_approval_site = ApiarySiteOnApproval.objects.create(
                                            #id=site_number,
                                            apiary_site=apiary_site,
                                            approval=approval,
                                            wkb_geometry=geometry,
                                            site_category = site_category,
                                            licensed_site=True if data['licensed_site'] else False,
                                            batch_no=data['batch_no'],
                                            approval_cpc_date=data['approval_cpc_date'] if data.approval_cpc_date else None,
                                            approval_minister_date=data['approval_minister_date'] if data.approval_minister_date else None,
                                            map_ref=data['map_ref'],
                                            forest_block=data['forest_block'],
                                            cog=data['cog'],
                                            roadtrack=data['roadtrack'],
                                            zone=data['zone'],
                                            catchment=data['catchment'],
                                            #dra_permit=data['dra_permit'],
                                            site_status=site_status,
                                            )
            #import ipdb; ipdb.set_trace()
            pa, pa_created = ProposalApiary.objects.get_or_create(proposal=proposal)

            intermediary_proposal_site = ApiarySiteOnProposal.objects.create(
                                            #id=site_number,
                                            apiary_site=apiary_site,
                                            #approval=approval,
                                            proposal_apiary=pa,
                                            wkb_geometry_draft=geometry,
                                            site_category_draft = site_category,
                                            wkb_geometry_processed=geometry,
                                            site_category_processed = site_category,
                                            licensed_site=True if data['licensed_site'] else False,
                                            batch_no=data['batch_no'],
                                            #approval_cpc_date=data['approval_cpc_date'],
                                            #approval_minister_date=data['approval_minister_date'],
                                            approval_cpc_date=data['approval_cpc_date'] if data.approval_cpc_date else None,
                                            approval_minister_date=data['approval_minister_date'] if data.approval_minister_date else None,
                                            map_ref=data['map_ref'],
                                            forest_block=data['forest_block'],
                                            cog=data['cog'],
                                            roadtrack=data['roadtrack'],
                                            zone=data['zone'],
                                            catchment=data['catchment'],
                                            site_status=site_status,
                                            #dra_permit=data['dra_permit'],
                                            )
            #import ipdb; ipdb.set_trace()

            apiary_site.latest_approval_link=intermediary_approval_site
            apiary_site.latest_proposal_link=intermediary_proposal_site
            if site_status == 'vacant':
                apiary_site.approval_link_for_vacant=intermediary_approval_site
                apiary_site.proposal_link_for_vacant=intermediary_proposal_site
            apiary_site.save()


        except Exception as e:
            logger.error('{}'.format(e))
            # import ipdb; ipdb.set_trace()
            return None

        return approval_affected

    def create_licence_pdf(self, approvals_created):
        # approvals_migrated = Approval.objects.filter(current_proposal__application_type__name=ApplicationType.APIARY, migrated=True)
        approvals_migrated = list(approvals_created)
        print('Total {} approval(s) for creating licence pdf: {}'.format(len(approvals_migrated), approvals_migrated))

        for idx, a in enumerate(approvals_migrated):
            a.generate_doc(a.current_proposal.submitter)
            print('{}, Created licence PDF for Approval: {}'.format(idx, a))



def create_invoice(proposal, payment_method='other'):
        """
        This will create and invoice and order from a basket bypassing the session
        and payment bpoint code constraints.
        """
        from ledger.checkout.utils import createCustomBasket
        from ledger.payments.invoice.utils import CreateInvoiceBasket
        from ledger_api_client.ledger_models import EmailUserRO as EmailUser

        now = timezone.now().date()
        line_items = [
            {'ledger_description': 'Migration Licence Charge Waiver - {} - {}'.format(now, proposal.lodgement_number),
             'oracle_code': 'N/A', #proposal.application_type.oracle_code_application,
             'price_incl_tax':  Decimal(0.0),
             'price_excl_tax':  Decimal(0.0),
             'quantity': 1,
            }
        ]

        user = EmailUser.objects.get(email__icontains='das@dbca.wa.gov.au')
        invoice_text = 'Migrated Permit/Licence Invoice'

        basket  = createCustomBasket(line_items, user, settings.PAYMENT_SYSTEM_ID)
        order = CreateInvoiceBasket(payment_method=payment_method, system=settings.PAYMENT_SYSTEM_PREFIX).create_invoice_and_order(basket, 0, None, None, user=user, invoice_text=invoice_text)

        return order
    


