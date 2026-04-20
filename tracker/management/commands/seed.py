from django.core.management.base import BaseCommand
from tracker.models import Category

class Command(BaseCommand):
    help = 'Seeds the database with the 4 default study categories'

    def handle(self, *args, **kwargs):
        categories = [
            {'name': 'DSA',  'color_code': '#4F46E5'},
            {'name': 'DS',   'color_code': '#0891B2'},
            {'name': 'ROB',  'color_code': '#16A34A'},
            {'name': 'EC',   'color_code': '#DC2626'},
        ]
        for cat in categories:
            obj, created = Category.objects.get_or_create(
                name=cat['name'],
                defaults={'color_code': cat['color_code']}
            )
            if created:
                self.stdout.write(self.style.SUCCESS(f'Created: {obj.get_name_display()}'))
            else:
                self.stdout.write(f'Already exists: {obj.get_name_display()}')

        self.stdout.write(self.style.SUCCESS('\nDone! All categories seeded.'))