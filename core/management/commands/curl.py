import pycurl

import sys
from bs4 import BeautifulSoup
import requests
from django.core.management import BaseCommand
from io import BytesIO
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from strgen import StringGenerator

def get_html_content(content, kill_script = False):
    soup = BeautifulSoup(content)
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

def curl(url, country, agent, rand):

    url = url.replace("&amp;", "&")
    username = 'lum-customer-theway_holdings-zone-nam-country-' + country
    password = '99oah6sz26i5'
    port = '22225'
    super_proxy = 'zproxy.luminati.io'
    url = url.replace("&amp;", "&")
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.PROXY, 'http://' + super_proxy + ':' + port)

    c.setopt(pycurl.PROXYUSERPWD, username + '-session-' + rand + ":" + password)

    c.setopt(pycurl.SSL_VERIFYPEER, 0)
    c.setopt(pycurl.SSL_VERIFYHOST, 0)
    c.setopt(pycurl.CONNECTTIMEOUT, 30)
    c.setopt(pycurl.FOLLOWLOCATION, 1)
    c.setopt(pycurl.MAXREDIRS, 10)
    c.setopt(pycurl.TIMEOUT, 80)
    c.setopt(pycurl.USERAGENT, agent)
    c.setopt(c.WRITEDATA, buffer)

    try:
        c.perform()
        result = buffer.getvalue()
        result = result.decode('utf-8').replace('\/', '/')
        result = get_html_content(result)
    except:
        type, value, tb = sys.exc_info()
        if hasattr(value, 'message'):
            result = "%s" % value.message
        else:
            result = 'Error'
    c.close()
    print(result)

class Command(BaseCommand):
    help = 'Running virtual clicks'
    def handle(self, *args, **options):
        rand = StringGenerator('[a-z]{4}|[0-9]{4}').render()[::8]
        #url = 'https://whatismyipaddress.com/ip-lookup'
        url = 'https://www.whoishostingthis.com/tools/user-agent/'
        country = 'gb'
        agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_2 like Mac OS X) AppleWebKit/601.1 (KHTML, like Gecko) CriOS/53.0.2785.109 Mobile/14A456 Safari/601.1.46'

        #proxy(url, country, agent, rand)
        curl(url, country, agent, rand)
        self.stdout.write('done')