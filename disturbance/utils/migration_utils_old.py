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
from dateutil.relativedelta import relativedelta
from decimal import Decimal

import logging
logger = logging.getLogger(__name__)


class ImportException(Exception):
    pass


class ApiaryLicenceReader():
    '''
    from disturbance.utils.migration_utils import ApiaryLicenceReader
    reader=ApiaryLicenceReader('disturbance/utils/csv/apiary_migration_file_01Sep20211-TEST.csv')
    reader.run_migration()
    '''
    def __init__(self, filename):
        self.filename = filename
        self.not_found = []
        #self.parks_not_found = []
        #self.org_lines = self._read_organisation_data()
        self.apiary_licence_lines = self._read_organisation_data()

        self.application_type = ApplicationType.objects.get(name=ApplicationType.APIARY)
        self.proposal_type = ProposalType.objects.all().order_by('name', '-version').distinct('name').get(name=self.application_type.name)

    def _write_to_migrated_apiary_licence_model(self):
        try:
            for row in self.apiary_licence_lines:
                #print(row)
                #import ipdb;ipdb.set_trace()
                #if row.get('permit_number') and row.get('licencee_type'):
                defaults = {
                    'permit_number': row['permit_number'],
                    'start_date': row['start_date'],
                    'expiry_date': row['expiry_date'],
                    'issue_date': row['issue_date'],
                    'status': row['status'].lower(),
                    'latitude': row['latitude'],
                    'longitude': row['longitude'],
                    'trading_name': row['trading_name'],
                    'licencee': row['licencee'],
                    'abn': row['abn'],
                    'first_name': row['first_name'],
                    'last_name': row['last_name'],
                    'address_line1': row['address_line1'],
                    'address_line2': row['address_line2'],
                    'address_line3': row['address_line3'],
                    'suburb': row['suburb'],
                    'state': row['state'],
                    'country': row['country'],
                    'postcode': row['postcode'],
                    'phone_number1': row['phone_number1'],
                    'phone_number2': row['phone_number2'],
                    'mobile_number': row['mobile_number'],
                    'email': row['email'],
                    'licencee_type': row['licencee_type'],
                }

                if row.get('licencee_type'):
                        #and (
                        #(row.get('licencee') and row.get('abn')) or 
                        #not row.get('licencee')
                        #):
                    licence = MigratedApiaryLicence.objects.create(**defaults)

#                    licence, created = MigratedApiaryLicence.objects.get_or_create(
#                        #**row_values
#                        #permit_number = row['permit_number'],
#                        defaults = {
#                            'permit_number': row['permit_number'],
#                            'start_date': row['start_date'],
#                            'expiry_date': row['expiry_date'],
#                            'issue_date': row['issue_date'],
#                            'status': row['status'].lower(),
#                            'latitude': row['latitude'],
#                            'longitude': row['longitude'],
#                            'trading_name': row['trading_name'],
#                            'licencee': row['licencee'],
#                            'abn': row['abn'],
#                            'first_name': row['first_name'],
#                            'last_name': row['last_name'],
#                            'address_line1': row['address_line1'],
#                            'address_line2': row['address_line2'],
#                            'address_line3': row['address_line3'],
#                            'suburb': row['suburb'],
#                            'state': row['state'],
#                            'country': row['country'],
#                            'postcode': row['postcode'],
#                            'phone_number1': row['phone_number1'],
#                            'phone_number2': row['phone_number2'],
#                            'mobile_number': row['mobile_number'],
#                            'email': row['email'],
#                            'licencee_type': row['licencee_type'],
#                            }
#                        )
#                    if not created:
#                        row.update({'previously_migrated': True})
#                        logger.warning('Record already exists, so not imported')
#                        logger.warning('Main {}'.format(row))
#                        #print('Main {}'.format(data))

                else:
                    #print(row)
                    #raise ImportException("Entry is not a valid organisation or individual licence record")
                    raise ImportException(row)

        except Exception as e:
            import ipdb; ipdb.set_trace()
            print(e)

    def run_migration(self):
        with transaction.atomic():
            try:
                #import ipdb; ipdb.set_trace()
                self._write_to_migrated_apiary_licence_model()
                self._create_licences()
                self._create_licence_pdf()
                #import denied sites
            except:
                import ipdb; ipdb.set_trace()
                raise Exception

    def _verify_data(self, verify=False):
        lines=[]
        with open(self.filename) as csvfile:
            reader = csv.reader(csvfile, delimiter=str(':'))
            header = next(reader) # skip header
            #import ipdb; ipdb.set_trace()
            error_lines=[]
            for idx, row in enumerate(reader):
                #import ipdb; ipdb.set_trace()
                try:
                    #if not row[0].startswith('#') and row[4].strip().lower() == 'current':
                    if not row[0].startswith('#'):
                        data={}
                        start_date_raw = row[1].strip()
                        expiry_date_raw = row[2].strip()
                        issue_date_raw = row[3].strip()
                        approval_cpc_date_raw = row[26].strip()
                        approval_minister_date_raw = row[27].strip()

                        if start_date_raw:
                            start_date = datetime.datetime.strptime(start_date_raw, '%d/%m/%Y').date()
                            data.update({'start_date': start_date})

                        if expiry_date_raw:
                            expiry_date = datetime.datetime.strptime(expiry_date_raw, '%d/%m/%Y').date()
                            data.update({'expiry_date': expiry_date})

                        if issue_date_raw:
                            issue_date = datetime.datetime.strptime(issue_date_raw.strip(), '%d/%m/%Y').date()
                            data.update({'issue_date': issue_date})
                        else:
                            data.update({'issue_date': start_date})

                        if approval_cpc_date_raw:
                            approval_cpc_date = datetime.datetime.strptime(approval_cpc_date_raw, '%d/%m/%Y').date()
                            data.update({'approval_cpc_date': approval_cpc_date})
                        else:
                            data.update({'approval_cpc_date': None})

                        if approval_minister_date_raw:
                            approval_minister_date = datetime.datetime.strptime(approval_minister_date_raw, '%d/%m/%Y').date()
                            data.update({'approval_minister_date': approval_minister_date})
                        else:
                            data.update({'approval_minister_date': None})

                except Exception as e:
                    error_lines.append(row)
                    import ipdb; ipdb.set_trace()

        print(len(error_lines))
        return lines

    def _read_organisation_data(self, verify=False):
        lines=[]
        try:
            '''
            Example csv
                address, town/city, state (WA), postcode, org_name, abn, trading_name, first_name, last_name, email, phone_number
                123 Something Road, Perth, WA, 6100, Import Test Org 3, 615503, DDD_03, john, Doe_1, john.doe_1@dbca.wa.gov.au, 08 555 5555

                File No:Licence No:Expiry Date:Term:Trading Name:Licensee:ABN:Title:First Name:Surname:Other Contact:Address 1:Address 2:Address 3:Suburb:State:Country:Post:Telephone1:Telephone2:Mobile:Insurance Expiry:Survey Cert:Name:SPV:ATAP Expiry:Eco Cert Expiry:Vessels:Vehicles:Email1:Email2:Email3:Email4
                2018/001899-1:HQ70324:28-Feb-21:3 YEAR:4 U We Do:4 U We Do Pty Ltd::MR:Petrus:Grobler::Po Box 2483:::ESPERANCE:WA:AUSTRALIA:6450:458021841:::23-Jun-18::::30-Jun-18::0:7:groblerp@gmail.com:::
            To test:
                from commercialoperator.components.proposals.models import create_organisation_data
                create_migration_data('commercialoperator/utils/csv/orgs.csv')
            '''
            with open(self.filename) as csvfile:
                reader = csv.reader(csvfile, delimiter=str(':'))
                header = next(reader) # skip header
                #import ipdb; ipdb.set_trace()
                error_lines=[]
                for idx, row in enumerate(reader):
                    #import ipdb; ipdb.set_trace()
                    try:
                        #if not row[0].startswith('#') and row[4].strip().lower() == 'current':
                        if not row[0].startswith('#') and not row[7].strip() == 'AJ & DE Dowsett':
                            data={}
                            data.update({'permit_number': row[0].strip() if row[0].strip()!='' else None})
                            start_date_raw = row[1].strip()
                            if start_date_raw:
                                start_date = datetime.datetime.strptime(start_date_raw, '%d/%m/%Y').date()
                                data.update({'start_date': start_date})
                            else:
                                continue
                            expiry_date_raw = row[2].strip()
                            if expiry_date_raw:
                                expiry_date = datetime.datetime.strptime(row[2].strip(), '%d/%m/%Y').date()
                                data.update({'expiry_date': expiry_date})
                            else:
                                data.update({'expiry_date': datetime.date.today()})

                            try:
                                issue_date = datetime.datetime.strptime(row[3].strip(), '%d/%m/%Y').date()
                                data.update({'issue_date': issue_date})
                            # set issue_date to start_date
                            except:
                                data.update({'issue_date': start_date})

                            try:
                                tmp = data['expiry_date']
                            except Exception as e:
                                import ipdb; ipdb.set_trace()

                            data.update({'status': row[4].strip().capitalize()})
                            # JM switched round the below for the csv file provided by Ashlee dated 01Sep2021
                            data.update({'latitude': row[6].translate(string.whitespace)})
                            data.update({'longitude': row[5].translate(string.whitespace)})
                            #data.update({'file_no': row[0].translate(None, string.whitespace)})
                            #data.update({'licence_no': row[1].translate(None, string.whitespace)})
                            #data.update({'expiry_date': row[2].strip()})
                            #data.update({'term': row[3].strip()})


                            data.update({'abn': row[9].translate(string.whitespace).replace(' ','')})
                            data.update({'trading_name': row[7].strip()})
                            if row[8].strip() != '':
                                data.update({'licencee': row[8].strip()})
                            else:
                                # set same as Trading Name
                                #data.update({'licencee': row[7].strip()})
                                data.update({'licencee': row[7].strip() + '(' + data['abn'] + ')'})

                            #data.update({'title': row[10].strip()})
                            first_name_raw = row[10].strip()
                            if first_name_raw:
                                first_name_split = first_name_raw.split('&')
                                data.update({'first_name': first_name_split[0].strip().capitalize()})
                            #data.update({'first_name': row[10].strip().capitalize()})
                            last_name_raw = row[11].strip()
                            if last_name_raw:
                                last_name_split = last_name_raw.split('&')
                                data.update({'last_name': last_name_raw.strip().capitalize()})
                            #data.update({'other_contact': row[12].strip()})
                            #import ipdb; ipdb.set_trace()
                            data.update({'address_line1': row[13].strip()})
                            data.update({'address_line2': row[14].strip()})
                            data.update({'address_line3': row[15].strip()})
                            data.update({'suburb': row[16].strip().capitalize()})
                            data.update({'state': row[17].strip()})

                            country_raw = ' '.join([i.lower().capitalize() for i in row[18].strip().split()])
                            #if country == 'A':
                                #country = 'Australia'
                            country_str = 'Australia' if country_raw.lower().startswith('a') else country_raw
                            country=Country.objects.get(printable_name__icontains=country_str)
                            data.update({'country': country.iso_3166_1_a2}) # 2 char 'AU'
                            if row[19].translate(string.whitespace) != '':
                                data.update({'postcode': row[19].translate(string.whitespace)})
                            else:
                                data.update({'postcode': '6000'})
                            data.update({'phone_number1': row[20].translate(b' -()')})
                            data.update({'phone_number2': row[21].translate(b' -()')})
                            data.update({'mobile_number': row[22].translate(b' -()')})

                            emails = row[23].translate(b' -()').replace(';', ',').split(',')
                            #import ipdb; ipdb.set_trace()
                            if row[24].translate(b' -()').capitalize() == '':
                                # This is a Permit
                                data.update({'licensed_site': False})
                            else:
                                data.update({'licensed_site': True})

                            # batch_no:approval_cpc_date:approval_minister_date:map_ref:forest_block:cog:roadtrack:zone:catchment:dra_permit
                            data.update({'batch_no': row[25].strip()})
                            approval_cpc_date_raw = row[26].strip()
                            try:
                                if approval_cpc_date_raw:
                                    approval_cpc_date = datetime.datetime.strptime(approval_cpc_date_raw, '%d/%m/%Y').date()
                                    data.update({'approval_cpc_date': approval_cpc_date})
                                else:
                                    data.update({'approval_cpc_date': None})
                                approval_minister_date_raw = row[27].strip()
                            except Exception as e:
                                print(e)
                                import ipdb; ipdb.set_trace()

                            if approval_minister_date_raw:
                                approval_minister_date = datetime.datetime.strptime(approval_minister_date_raw, '%d/%m/%Y').date()
                                data.update({'approval_minister_date': approval_minister_date})
                            else:
                                data.update({'approval_minister_date': None})
                            data.update({'map_ref': row[28].strip()})
                            data.update({'forest_block': row[29].strip()})
                            data.update({'cog': row[30].strip()})
                            data.update({'roadtrack': row[31].strip()})
                            data.update({'zone': row[32].strip()})
                            data.update({'catchment': row[33].strip()})
                            data.update({'dra_permit': row[34].strip() if row[34].strip() else False})
                            data.update({'site_status': settings.SITE_STATUS_SUSPENDED if row[35].strip() else settings.SITE_STATUS_CURRENT})

                            #pli_expiry_date_raw = row[25].strip()
                            #if pli_expiry_date_raw:
                            #    pli_expiry_date = datetime.datetime.strptime(pli_expiry_date_raw, '%d/%m/%Y').date()
                            #    data.update({'pli_expiry_date': pli_expiry_date})

                            #for num, email in enumerate(emails, 1):
                             #   data.update({'email{}'.format(num): email.lower()})
                            if emails:
                                data.update({'email': emails[0].strip().lower()})
                            # Org or individual record
                            if data.get('licencee')!='' and data.get('abn')!='':
                                data.update({'licencee_type': 'organisation'})
                            #elif not data.get('licencee'):
                            elif data.get('abn')=='':
                                data.update({'licencee_type': 'individual'})
                            else:
                                #import ipdb; ipdb.set_trace()
                                raise ImportException("Entry is not a valid organisation or individual licence record")

                            #if data['abn'] != '':
                            lines.append(data) # must be an org
                            ##else:
                            ##   print data['first_name'], data['last_name'], data['email1'], data['abn']
                            ##   print
                    except Exception as e:
                        print(idx)
                        print(e)
                        print(row)
                        error_lines.append(row)
                        print

        except Exception as e:
            import ipdb; ipdb.set_trace()
            #logger.info('{}'.format(e))
            if data:
                logger.error('{}'.format(e))
                logger.error('Main {}'.format(data))
                #print('Main {}'.format(data))
            else:
                print(e)
            raise

        print(len(error_lines))
        return lines

    def _create_individual(self, data, count, debug=False):
        try:
            #if data['email1'] == 'info@safaris.net.au':
            #    import ipdb; ipdb.set_trace()
            user, created_user = EmailUser.objects.get_or_create(email=data['email'],
                    defaults={'first_name': data['first_name'], 'last_name': data['last_name'], 'phone_number': data['phone_number1'], 'mobile_number': data['mobile_number']}
                )
            return user
            #print '{} {} {}'.format(data['first_name'], data['last_name'], EmailUser.objects.filter(first_name=data['first_name'], last_name=data['last_name']))
            #print data['email1']
        except Exception:
            #print 'user: {}   *********** 1 *********** FAILED'.format(data['email'])
            logger.error('user: {}   *********** 1 *********** FAILED'.format(data['email']))

    def _create_organisation(self, data, count, debug=False):
        #import ipdb; ipdb.set_trace()
        if debug:
            import ipdb; ipdb.set_trace()
        try:
            #if data['email1'] == 'info@safaris.net.au':
            #    import ipdb; ipdb.set_trace()
            user, created_user = EmailUser.objects.get_or_create(email=data['email'],
                    defaults={'first_name': data['first_name'], 'last_name': data['last_name'], 'phone_number': data['phone_number1'], 'mobile_number': data['mobile_number']}
                )
            #print '{} {} {}'.format(data['first_name'], data['last_name'], EmailUser.objects.filter(first_name=data['first_name'], last_name=data['last_name']))
            #print data['email1']
        except Exception:
            print('user: {}   *********** 1 *********** FAILED'.format(data['email']))
            #return

        lo=ledger_organisation.objects.filter(abn=data['abn'])
        if lo.count() > 0:
            lo = lo[0]
        else:
            try:
                #print 'Country: {}'.format(data['country'])
                #country_str = 'Australia' if country_raw.lower().startswith('a') else country_raw
                country=Country.objects.get(iso_3166_1_a2=data.get('country'))

                #country=Country.objects.get(printable_name__icontains=data['country'])
                oa, created = OrganisationAddress.objects.get_or_create(
                    line1=data['address_line1'],
                    locality=data['suburb'],
                    postcode=data['postcode'] if data['postcode'] else '0000',
                    defaults={
                        'line2': data['address_line2'],
                        'line3': data['address_line3'],
                        'state': data['state'],
                        'country': country.code,
                    }
                )
            except MultipleObjectsReturned:
                oa = OrganisationAddress.objects.filter(
                    line1=data['address_line1'],
                    locality=data['suburb'],
                    postcode=data['postcode'] if data['postcode'] else '0000',
                    line2=data['address_line2'],
                    line3=data['address_line3'],
                    state=data['state'],
                    country=country.code
                ).first()

            except Exception:
                print('Country 2: {}'.format(data['country']))
                raise

                lo, created_lo = ledger_organisation.objects.create(
                    abn=data['abn'],
                    name=data['licencee'],
                    postal_address=oa,
                    billing_address=oa,
                    trading_name=data['trading_name'],
                )
                org, created_org = Organisation.objects.get_or_create(organisation=lo)

        abn_existing = []
        abn_new = []
        try:
            lo=ledger_organisation.objects.get(abn=data['abn'])

            for org in lo.organisation_set.all():
                for contact in org.contacts.all():
                    if 'ledger.dpaw.wa.gov.au' in contact.email and data['email'] and org.contacts.filter(email=data['email']).count()==0:
                        contact.email = data['email']
                        contact.save()

            abn_existing.append(data['abn'])
            print('{}, Existing ABN: {}'.format(count, data['abn']))
            process = False
        except Exception as e:
            print('{}, Add ABN: {}'.format(count, data['abn']))
        #print 'DATA: {}'.format(data)

        try:
            #print 'Country: {}'.format(data['country'])
            #country_str = 'Australia' if data['country'].lower().startswith('a') else data['country']
            #country=Country.objects.get(printable_name__icontains=country_str)
            country=Country.objects.get(iso_3166_1_a2=data.get('country'))
            oa, created = OrganisationAddress.objects.get_or_create(
                line1=data['address_line1'],
                locality=data['suburb'],
                postcode=data['postcode'] if data['postcode'] else '0000',
                defaults={
                    'line2': data['address_line2'],
                    'line3': data['address_line3'],
                    'state': data['state'],
                    'country': country.code,
                }
            )
        except MultipleObjectsReturned:
            oa = OrganisationAddress.objects.filter(
                line1=data['address_line1'],
                locality=data['suburb'],
                postcode=data['postcode'] if data['postcode'] else '0000',
                line2=data['address_line2'],
                line3=data['address_line3'],
                state=data['state'],
                country=country.code
            ).first()

        except Exception as e:
            print('Country 2: {}'.format(data['country']))
            import ipdb; ipdb.set_trace()
            raise

        try:
            #import ipdb; ipdb.set_trace()
            data['licencee'] = data['licencee'] + ' ' if ledger_organisation.objects.filter(name=data['licencee']) else data['licencee']

            try:
                lo = ledger_organisation.objects.get(abn=data['abn'])
            except:
                lo, created = ledger_organisation.objects.get_or_create(
                    abn=data['abn'],
                    defaults={
                        'name': data['licencee'],
                        'postal_address': oa,
                        'billing_address': oa,
                        'trading_name': data['trading_name']
                    }
                )


#            lo, created = ledger_organisation.objects.get_or_create(
#                abn=data['abn'],
#                defaults={
#                    'name': data['licencee'],
#                    'postal_address': oa,
#                    'billing_address': oa,
#                    'trading_name': data['trading_name']
#                }
#            )

        except Exception as e:
            print('Error creating Organisation: {} - {}'.format(data['licencee'], data['abn']))
            raise

        try:
            org, created = Organisation.objects.get_or_create(organisation=lo)
        except Exception as e:
            print('Error: Org: {}'.format(org))
            #raise

        try:
            #Organisation.objects.get(id=12).delegates.filter().delete()
            #import ipdb; ipdb.set_trace()
            #user_delegate_ids = list(UserDelegation.objects.filter(organisation=org)[1:].values_list('id', flat=True))
            #if len(user_delegate_ids)>0:
            #    UserDelegation.objects.filter(id__in=user_delegate_ids).delete()

            UserDelegation.objects.filter(organisation=org).delete()
            delegate, created = UserDelegation.objects.get_or_create(organisation=org, user=user)
        except Exception as e:
            import ipdb; ipdb.set_trace()
            print('Delegate Creation Failed: {}'.format(user))
            #raise

        try:
            oc, created = OrganisationContact.objects.get_or_create(
                organisation=org,
                #email=data['email1'],
                email=delegate.user.email,
                defaults={
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'phone_number': user.phone_number,
                    'mobile_number': user.mobile_number if data['mobile_number'] else '',
                    'user_status': 'active',
                    'user_role': 'organisation_admin',
                    'is_admin': True
                }
            )
            if oc and 'ledger.dpaw.wa.gov.au' in oc.email:
                oc.email = delegate.user.email
                oc.save()

            if oc and not created:
                oc.user_role ='organisation_admin'
                oc.is_admin = True
                oc.user_status ='active'
                oc.save()

        except Exception as e:
            #import ipdb; ipdb.set_trace()
            print('Org Contact: {}'.format(user))
            #raise

        #return abn_new, abn_existing
        return org, user


    def _migrate_approval(self, data, submitter, applicant=None, proxy_applicant=None):
        from disturbance.components.approvals.models import Approval
        #import ipdb; ipdb.set_trace()
        #application_type=ApplicationType.objects.get(name=ApplicationType.APIARY)
        #qs_proposal_type = ProposalType.objects.all().order_by('name', '-version').distinct('name')
        #proposal_type = qs_proposal_type.get(name=application_type.name)
        try:
            t = time.process_time()
            print('******************************************************** 1: {}'.format(time.process_time() - t)); t = time.process_time()

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
                                    'issue_date':data['issue_date'],
                                    'expiry_date':data['expiry_date'],
                                    'start_date':data['start_date'],
                                    #'submitter':submitter,
                                    'current_proposal':proposal,
                                    }
                            )
            else:
                import ipdb; ipdb.set_trace()

            if 'PM' not in proposal.lodgement_number:
                proposal.lodgement_number = proposal.lodgement_number.replace('P', 'PM') # Application Migrated
            proposal.approval= approval
            proposal.processing_status='approved'
            proposal.customer_status='approved'
            proposal.migrated=True
            proposal.proposed_issuance_approval = {
                    'start_date': data['start_date'].strftime('%d-%m-%Y'),
                    'expiry_date': data['expiry_date'].strftime('%d-%m-%Y'),
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
            geometry = GEOSGeometry('POINT(' + str(data['latitude']) + ' ' + str(data['longitude']) + ')', srid=4326)
            apiary_site = ApiarySite.objects.create()
            site_category = get_category(geometry)
            intermediary_approval_site = ApiarySiteOnApproval.objects.create(
                                            apiary_site=apiary_site,
                                            approval=approval,
                                            wkb_geometry=geometry,
                                            site_category = site_category,
                                            licensed_site=data['licensed_site'],
                                            batch_no=data['batch_no'],
                                            approval_cpc_date=data['approval_cpc_date'],
                                            approval_minister_date=data['approval_minister_date'],
                                            map_ref=data['map_ref'],
                                            forest_block=data['forest_block'],
                                            cog=data['cog'],
                                            roadtrack=data['roadtrack'],
                                            zone=data['zone'],
                                            catchment=data['catchment'],
                                            dra_permit=data['dra_permit'],
                                            site_status=data['site_status'],
                                            )
            #import ipdb; ipdb.set_trace()
            pa, pa_created = ProposalApiary.objects.get_or_create(proposal=proposal)
            #if pa_created:
            #    # since this is an application level field
            #    pa.public_liability_insurance_expiry_date = data['pli_expiry_date'].strftime('%d-%m-%Y') 

            intermediary_proposal_site = ApiarySiteOnProposal.objects.create(
                                            apiary_site=apiary_site,
                                            #approval=approval,
                                            proposal_apiary=pa,
                                            wkb_geometry_draft=geometry,
                                            site_category_draft = site_category,
                                            wkb_geometry_processed=geometry,
                                            site_category_processed = site_category,
                                            licensed_site=data['licensed_site'],
                                            batch_no=data['batch_no'],
                                            approval_cpc_date=data['approval_cpc_date'],
                                            approval_minister_date=data['approval_minister_date'],
                                            map_ref=data['map_ref'],
                                            forest_block=data['forest_block'],
                                            cog=data['cog'],
                                            roadtrack=data['roadtrack'],
                                            zone=data['zone'],
                                            catchment=data['catchment'],
                                            dra_permit=data['dra_permit'],
                                            )

            apiary_site.latest_approval_link=intermediary_approval_site
            apiary_site.latest_proposal_link=intermediary_proposal_site
            apiary_site.save()

            #print('******************************************************** 5: {}'.format(time.process_time() - t))
            #t = time.process_time()

            #approval.generate_doc(submitter)

            print('******************************************************** 6: {}'.format(time.process_time() - t)); t = time.process_time()

        except Exception as e:
            logger.error('{}'.format(e))
            import ipdb; ipdb.set_trace()
            return None

        return approval

    def _create_licences(self):
        count = 1
        for data in self.apiary_licence_lines:
        #for data in self.apiary_licence_lines[1301:1306]:
        #for data in self.apiary_licence_lines[1304:]:
            #result_qs = MigratedApiaryLicence.objects.filter(permit_number=data['permit_number'])
            #import ipdb; ipdb.set_trace()
            # do not run if row has already been processed in a previous migration
            if not data.get('previously_migrated'):
                if data.get('licencee_type') == 'organisation':
                    org, submitter = self._create_organisation(data, count)
                    self._migrate_approval(data=data, submitter=submitter, applicant=org, proxy_applicant=None)
                    print("Permit number {} migrated".format(data.get('permit_number')))
                    print
                    print

                elif data.get('licencee_type') == 'individual':
                    user = self._create_individual(data, count)
                    self._migrate_approval(data=data, submitter=user, applicant=None, proxy_applicant=user)
                    print("Permit number {} migrated".format(data.get('permit_number')))

                else:
                    # declined and not to be reissued
                    status = data['status']
            count += 1


    def _create_licence_pdf(self):
        approvals_migrated = Approval.objects.filter(current_proposal__application_type__name=ApplicationType.APIARY, migrated=True)
        print('Total Approvals: {}'.format(approvals_migrated))
        for idx, a in enumerate(approvals_migrated):
            a.generate_doc(a.current_proposal.submitter)
            print('{}, Created PDF for Approval {}'.format(idx, a))



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
        invoice_text = 'Migration Invoice'

        basket  = createCustomBasket(line_items, user, settings.PAYMENT_SYSTEM_ID)
        order = CreateInvoiceBasket(payment_method=payment_method, system=settings.PAYMENT_SYSTEM_PREFIX).create_invoice_and_order(basket, 0, None, None, user=user, invoice_text=invoice_text)

        return order
    

class ApiaryLicenceCsvVerifier():
    '''
    from disturbance.utils.migration_utils import ApiaryLicenceCsvVerifier
    reader=ApiaryLicenceCsvVerifier('disturbance/utils/csv/apiary_migration_file_01Sep20211-TEST.csv')
    '''
    def __init__(self, filename):
        self.filename = filename
        self.not_found = []
        self.apiary_licence_lines = self._verify_data()

    def _verify_data(self, verify=False):
        lines=[]
        unique_abn_list=[]
        with open(self.filename) as csvfile:
            reader = csv.reader(csvfile, delimiter=str(':'))
            header = next(reader) # skip header
            error_lines=[]
            for idx, row in enumerate(reader):
                #import ipdb; ipdb.set_trace()
                try:
                    #if not row[0].startswith('#') and row[4].strip().lower() == 'current':
                    if not row[0].startswith('#') and not row[7].strip() == 'AJ & DE Dowsett':
                        data={}
                        start_date_raw = row[1].strip()
                        expiry_date_raw = row[2].strip()
                        issue_date_raw = row[3].strip()
                        approval_cpc_date_raw = row[26].strip()
                        approval_minister_date_raw = row[27].strip()

                        if start_date_raw:
                            start_date = datetime.datetime.strptime(start_date_raw, '%d/%m/%Y').date()
                            data.update({'start_date': start_date})

                        if expiry_date_raw:
                            expiry_date = datetime.datetime.strptime(expiry_date_raw, '%d/%m/%Y').date()
                            data.update({'expiry_date': expiry_date})

                        if issue_date_raw:
                            issue_date = datetime.datetime.strptime(issue_date_raw.strip(), '%d/%m/%Y').date()
                            data.update({'issue_date': issue_date})
                        else:
                            data.update({'issue_date': start_date})

                        if approval_cpc_date_raw:
                            approval_cpc_date = datetime.datetime.strptime(approval_cpc_date_raw, '%d/%m/%Y').date()
                            data.update({'approval_cpc_date': approval_cpc_date})
                        else:
                            data.update({'approval_cpc_date': None})

                        if approval_minister_date_raw:
                            approval_minister_date = datetime.datetime.strptime(approval_minister_date_raw, '%d/%m/%Y').date()
                            data.update({'approval_minister_date': approval_minister_date})
                        else:
                            data.update({'approval_minister_date': None})

                        data.update({'abn': row[9].translate(string.whitespace).replace(' ','')})
                        if data['abn'] not in unique_abn_list:
                            unique_abn_list.append(data['abn'])

                        lines.append(data) # must be an org

                except Exception as e:
                    error_lines.append(row)
                    import ipdb; ipdb.set_trace()
                    print(e)

        print('Error Lines: {}'.format(len(error_lines)))
        print('Unique ABNs: {}'.format(len(unique_abn_list)))
        print('Lines: {}'.format(len(lines)))
        print(unique_abn_list)
        return lines


