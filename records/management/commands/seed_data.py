import random
from django.core.management.base import BaseCommand
from records.models import DailyRecord
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Seeds the database with sample data for 3 months if the database is empty.'

    def handle(self, *args, **options):
        # Check if there is any data first
        if DailyRecord.objects.exists():
            self.stdout.write(self.style.SUCCESS('Database already contains data. Skipping seeding.'))
            return

        self.stdout.write('Database is empty. Seeding with sample data...')

        RATING_CHOICES = ['S', 'A', 'B', 'C', 'D']
        WEATHER_CHOICES = ['sunny', 'cloudy', 'rainy']
        MEDICINE_CHOICES = ['yes', 'no', 'unknown']

        start_date = date.today() - timedelta(days=90)

        last_pressure = 1010.0

        for i in range(90):
            current_date = start_date + timedelta(days=i)

            pressure_change = random.uniform(-2.5, 2.5)
            max_pressure = last_pressure + pressure_change
            min_pressure = max_pressure - random.uniform(0.5, 2.0)
            last_pressure = max_pressure

            wife_mood = random.choice(RATING_CHOICES)
            if pressure_change < -1.5:
                wife_mood = random.choice(['C', 'D'])
            elif pressure_change > 1.5:
                wife_mood = random.choice(['S', 'A'])

            DailyRecord.objects.create(
                date=current_date,
                weather=random.choice(WEATHER_CHOICES),
                max_pressure=round(max_pressure, 1),
                min_pressure=round(min_pressure, 1),
                max_temperature=random.uniform(15.0, 30.0),
                min_temperature=random.uniform(5.0, 15.0),
                humidity=random.randint(40, 90),
                pollen=random.choice(RATING_CHOICES),
                pm25=random.choice(RATING_CHOICES),
                my_mood=random.choice(RATING_CHOICES),
                wife_mood=wife_mood,
                headache_medicine=random.choice(MEDICINE_CHOICES),
                mishap=random.choice([True, False]),
                diary=f'This is a sample diary entry for {current_date}.'
            )

        self.stdout.write(self.style.SUCCESS('Successfully seeded 90 days of sample data.'))
