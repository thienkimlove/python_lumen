
import re
import time

import redis
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from gevent.pool import Pool
from strgen import StringGenerator
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs


from django.core.management.base import BaseCommand
from core.models import Log

def regex_check(content):
    regex = [
        r"window\.location\.replace\([\"\']?(https?\:\/\/[^\"\']+)",
        r"window.location\s*=\s*[\"\']?(https?\:\/\/[^\"\']+)",
        r"window\.top\.location\.replace\([\"\']?(https?\:\/\/[^\"\']+)",
        r"window.top.location\s*=\s*[\"']?(https?\:\/\/[^\"']+)",
        r"meta\s*http-equiv\s*=\s*[\"\']?refresh[\"\']?\s*content=[\"\']?\d+;(?:url\s*=)?\s*[\'\"]?(https?\:\/\/[^\"\']+)",
        r"meta\.content\s*=\s*[\"\']?\d+;\s*(?:url\s*=)?\s*[\'\"]?(https?:\/\/[^\"\']+)",
        r"meta\s*http-equiv\s*=\s*[\"\']?refresh[\"\']?\s*content=[\"\']?\d+;\s*(?:url\s*=)?\s*[\'\"]?(https?:\/\/[^\"\']+)",
        r"location.href\s*=\s*[\"']?(https?\:\/\/[^\"']+)"
    ]
    find = None
    for reg in regex:
        result = re.findall(reg, content, re.IGNORECASE)
        if result:
            find = result[0].replace("'", '')
            break
    return find

def get_html_content(content, kill_script = False):
    soup = BeautifulSoup(content, "html.parser")
    if kill_script:
        remove_elements = ["script", "style", 'image']
    else:
        remove_elements = ["style", 'image']
    # kill all script and style elements
    for script in soup(remove_elements):
        script.extract()    # rip it out

    # get text
    text = soup.get_text()

    # break into lines and remove leading and trailing space on each
    lines = (line.strip() for line in text.splitlines())
    # break multi-headlines into a line each
    chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
    # drop blank lines
    return '\n'.join(chunk for chunk in chunks if chunk)

def proxy(url, country, agent, rand):

    credentials = 'lum-customer-theway_holdings-zone-nam-country-' + country.lower() + '-session-' + rand.lower() + ':99oah6sz26i5'


    proxies = {
        'http':  credentials + "@zproxy.luminati.io:22225",
        'https': credentials + "@zproxy.luminati.io:22225"
    }
    session = requests.session()
    session.max_redirects = 10
    session.verify = False
    session.timeout = 60
    session.headers.update({'User-Agent': agent})
    session.proxies.update(proxies)

    url_short = ''

    try:
        o = urlparse(url)
        query = parse_qs(o.query)
        url_short = o._replace(query=None).geturl()
        g = session.get(url_short, params=query)
        result = get_html_content(g.content)
        result = result.replace('\/', '/')

    except requests.exceptions.Timeout as e:
        # Maybe set up for a retry, or continue in a retry loop
        result = "Error with request %s" % e
    except requests.exceptions.TooManyRedirects as e:
        # Tell the user their URL was bad and try a different one
        result = "Error with request %s" % e
    except requests.exceptions.ContentDecodingError as e:
        # Tell the user their URL was bad and try a different one
        result = "Error with request %s" % e
    except requests.exceptions.InvalidURL as e:
        # Tell the user their URL was bad and try a different one
        result = "Error with request %s" % e
    except UnicodeError as err:
        result = "Error in unicode {}".format(err) + " for url=" + url + ' short_url=' + url_short
    except Exception as err:
        result = "Error in proxy {}".format(err) + " for url=" + url

    return result

def virtual_curl(country, url, rand, agent, redirection=0):

    is_ok = True
    try:
        result = proxy(url, country, agent, rand)
        if not result:
            is_ok = False
    except Exception as err:
        result = "Error  {}".format(err)
        is_ok = False

    if redirection < 6 and is_ok:
        check = regex_check(result)
        if check is not None:
            redirection = redirection + 1
            return virtual_curl(country, check, agent, rand, redirection)

    if len(result) > 2000 and is_ok:
        end_result = result[:2000]
    else:
        end_result = result

    return '{ source : '+ end_result +', url : ' + url + ' }'

def fetch_item(log_id, country, allow, link):

    rand = StringGenerator('[a-z]{4}|[0-9]{4}').render()[::8]

    agent_row = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_1 like Mac OS X) AppleWebKit/602.2.14 (KHTML, like Gecko) Mobile/14B72' if allow > 4 else 'Mozilla/5.0 (Linux; Android 5.0.1; SAMSUNG SM-N920K Build/LRX22C) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/3.4 Chrome/34.0.1847.118 Mobile Safari/537.36'

    user_country = country.lower().replace(' ', ',')
    if ',' in user_country:
        user_country = user_country.split(',')[0]
    response = virtual_curl(user_country, link, rand, agent_row)

    item = Log.objects.get(pk=log_id)
    item.agent = agent_row
    item.response = response
    item.sent = 1
    item.save()

class Command(BaseCommand):
    help = 'Running virtual clicks'
    def handle(self, *args, **options):

        start_time = time.time()

        redis_client = redis.Redis()
        timeout = 60 * 60 * 5  # five hours
        lock = redis_client.lock('virtual_click_process', timeout=timeout)
        have_lock = lock.acquire(blocking=False)
        if have_lock:
            requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
            #connection.allow_thread_sharing = True
            pool = Pool(4000)
            logs  = Log.objects.filter(sent__isnull=True).all()
            for log in logs:
                pool.spawn(fetch_item, log.id, log.country, log.allow, log.link)
            pool.join()
            lock.release()
        else:
            self.stdout.write(self.style.SUCCESS('Another process is running!'))

        end_time = time.time()
        self.stdout.write(self.style.SUCCESS('Successfully end clicks in "%s"' % (end_time - start_time)))