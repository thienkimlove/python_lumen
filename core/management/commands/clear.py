
import time

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Delete old logs'
    def handle(self, *args, **options):

        start_time = time.time()

        with connection.cursor() as cursor:
            cursor.execute("delete from lumen.logs where sent=1 order by id limit 1000000")
        self.stdout.write(self.style.SUCCESS('Completed!'))

        end_time = time.time()
        self.stdout.write(self.style.SUCCESS('Successfully end clicks in "%s"' % (end_time - start_time)))
