from django.core.management.base import BaseCommand
from records.models import DailyRecord

class Command(BaseCommand):
    help = 'Deletes all DailyRecord data from the database.'

    def handle(self, *args, **options):
        self.stdout.write('Deleting all daily records...')
        count, _ = DailyRecord.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'Successfully deleted {count} records.'))
