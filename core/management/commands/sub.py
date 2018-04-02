
import re
import time

import redis
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from gevent.pool import Pool
from strgen import StringGenerator
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, unquote


from django.core.management.base import BaseCommand
from django.core import management
from django.db import connection
from core.models import Log

def call_existed():
    management.call_command('basic', verbosity=0)

class Command(BaseCommand):
    help = 'Running virtual clicks'
    def handle(self, *args, **options):

        start_time = time.time()

        with connection.cursor() as cursor:
            cursor.execute("update logs set sent=0 where sent is null and process is null")
            cursor.execute("select count(*) from logs where sent=0 and process is null")
            count = cursor.fetchone()[0]

        i = count
        pool = Pool()
        while i > 100:
            pool.spawn(call_existed())
            i = i - 100
        pool.spawn(call_existed())
        pool.join()
        self.stdout.write(self.style.SUCCESS('Completed!'))

        end_time = time.time()
        self.stdout.write(self.style.SUCCESS('Successfully end clicks in "%s"' % (end_time - start_time)))
