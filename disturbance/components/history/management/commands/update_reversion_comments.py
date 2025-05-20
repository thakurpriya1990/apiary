""" This custom management command will iterate through model versions
    and add revision comments when certain fields change so that we 
    can filter based on this when showing a version history on the 
    frontend.

    Usage: ./manage_ds.py update_reversion_comments <app_label> <model_name> <records_to_process>

    Examples:
    
    Process versions for all proposals in the disturbance app

    ./manage_ds.py update_reversion_comments disturbance Proposal 0

    Process versions for proposals with pk=100 in the disturbance app

    ./manage_ds.py update_reversion_comments disturbance Proposal 100

    Todo: To make this fully generic, we would need to pass in the list
    of fields that we are checking for changes in. Currently it is checking
    procesing_status, assessor_data and comment_data (which are speficic to 
    a Proposal model)
"""
from django.apps import apps
from django.core.management.base import BaseCommand, CommandError
from reversion.models import Version
import csv

class Command(BaseCommand):
    help = 'Adds revision comments whenever a model version processing_status changes'

    def add_arguments(self, parser):
        parser.add_argument('app_label', nargs='+', type=str)
        parser.add_argument('model_name', nargs='+', type=str)
        parser.add_argument('pk', nargs='+', type=str)

    def handle(self, *args, **options):
        app_label = options['app_label'][0]
        model_name = options['model_name'][0]
        pk = int(options['pk'][0])
        self.stdout.write('app_label = %s' % app_label)
        self.stdout.write('model_name = %s' % model_name)
        comments_orig = []
        try:
            model = apps.get_model(app_label=app_label, model_name=model_name)
        except ValueError:
            raise CommandError('No model of name {} exists in the {} application.'.format(model_name, app_label))

        if 0 == pk:
            models = model.objects.all() # Process all 
        else:
            models = model.objects.filter(pk=pk) # add a slice to test with less records

        change_database = True # Make False for testing to avoid writing to database

        for instance in models:
            self.stdout.write('\nSelecting Versions for {} {}'.format(instance._meta.verbose_name_raw, instance.pk))
            versions = Version.objects.get_for_object(instance).select_related('revision') # .order_by('revision__date_created')
            for i, version in enumerate(versions):
                if i == 0:
                    self.stdout.write(self.style.WARNING('\n\tStatus change detected'))
                    if change_database:
                        self.stdout.write(self.style.SUCCESS('\tInserting: "processing_status: {}" into revision table'.format( version.field_dict['processing_status'])))
                        comments_orig.append([version.id, version.revision.id, version.revision.comment])
                        if(version.revision.comment):
                            version.revision.comment = 'processing_status: {}'.format( version.field_dict['processing_status'] ) + ', ' + version.revision.comment
                        else:
                            version.revision.comment = 'processing_status: {}'.format( version.field_dict['processing_status'] )
                        version.revision.save()
                if i>0:
                    if version.field_dict['processing_status'] != versions[i-1].field_dict['processing_status']:
                        self.stdout.write(self.style.WARNING('\n\tStatus change detected'))
                        if change_database:
                            self.stdout.write(self.style.SUCCESS('\tInserting: "processing_status: {}" into revision table'.format( version.field_dict['processing_status'])))
                            comments_orig.append([version.id, version.revision.id, version.revision.comment])
                            if(version.revision.comment):
                                version.revision.comment = 'processing_status: {}'.format( version.field_dict['processing_status'] ) + ', ' + version.revision.comment
                            else:
                                version.revision.comment = 'processing_status: {}'.format( version.field_dict['processing_status'] )
                            version.revision.save()
                        # We've already added a comment so no need to check other fields
                    elif version.field_dict['assessor_data'] != versions[i-1].field_dict['assessor_data'] and not version.field_dict['assessor_data'] is None:
                        #self.stdout.write(self.style.ERROR('\n{}\n\n{}\n'.format(version.field_dict['assessor_data'], versions[i-1].field_dict['assessor_data'])))
                        self.stdout.write(self.style.WARNING('\n\tAssessor Data change detected'))
                        if change_database:
                            self.stdout.write(self.style.SUCCESS('\tInserting: "assessor_data: Has changed - tagging with processing_status" into revision table'))
                            comments_orig.append([version.id, version.revision.id, version.revision.comment])
                            if(version.revision.comment):
                                version.revision.comment = version.revision.comment + ', ' + 'assessor_data: Has changed - tagging with processing_status'.format( version.field_dict['assessor_data'] )
                            else:
                                version.revision.comment = 'assessor_data: Has changed - tagging with processing_status'.format( version.field_dict['assessor_data'] )
                            version.revision.save()
                    elif version.field_dict['comment_data'] != versions[i-1].field_dict['comment_data'] and not version.field_dict['comment_data'] is None:
                        self.stdout.write(self.style.WARNING('\n\tComment Data change detected'))
                        if change_database:
                            self.stdout.write(self.style.SUCCESS('\tInserting: "comment_data: Has changed - tagging with processing_status" into revision table'.format( version.field_dict['comment_data'])))
                            comments_orig.append([version.id, version.revision.id, version.revision.comment])
                            if(version.revision.comment):
                                version.revision.comment = version.revision.comment + ', ' + 'comment_data: Has changed - tagging with processing_status'.format( version.field_dict['comment_data'] )
                            else:
                                version.revision.comment = 'comment_data: Has changed - tagging with processing_status'.format( version.field_dict['comment_data'] )
                            version.revision.save()

                self.stdout.write('\t{} {} - Date: {} Status: {}'.format(instance._meta.verbose_name_raw, \
                    instance.pk, version.revision.date_created, version.field_dict['processing_status']))


        with open("update_reversion_comments_orig.csv", "w") as f:
            writer = csv.writer(f)
            writer.writerows(comments_orig)

        self.stdout.write(self.style.SUCCESS('Finished processing {} records.'.format(len(models))))


