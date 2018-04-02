
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
        r"location.href\s*=\s*[\"']?(https?\:\/\/[^\"']+)",
        r"\.src\s*=\s*[\"\']?(https?\:\/\/[^\"\']+)"
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

    url = unquote(url)
    url = url.replace('&amp;', '&')

    url_short = ''
    result = None

    if 'itunes.apple.com' in url:
        result = 'Completed with URL=' + url

    if result is None:
        try:
            o = urlparse(url)
            query = parse_qs(o.query, True)
            url_short = o._replace(query=None).geturl()
            g = session.get(url_short, params=query)
            #result = get_html_content(g.content)
            result = g.content.decode('utf8').replace('\/', '/')

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

    if 'ogp.me/ns' in result:
        result = 'Completed with URL=' + url


    return result

def regex_without_scheme(content, url):
    special = [
        r"\s*content=[\"\']?\d+;(?:url\s*=)?\s*[\'\"]?([^\"\']+)"
    ]
    parse_url = urlparse(url)
    domain = '{uri.scheme}://{uri.netloc}'.format(uri=parse_url)
    find = None
    for reg in special:
        result = re.findall(reg, content, re.IGNORECASE)
        if result:
            find = result[0].replace("'", '')
            break
    if find is not None:
        find = domain + find
    return find

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
        else:
            special_check = regex_without_scheme(result, url)
            if special_check is not None:
                redirection = redirection + 1
                return virtual_curl(country, special_check, agent, rand, redirection)
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
        response = virtual_curl('gb', 'http://clk.myiads.com/click?a=75052433&o=76332999&sub_id=1ed93ab6c9b36e3dbefd21d74afe17d6&sub_id2=Tq6I9AtHPe12VODH&idfa=', '434343', '')
        print(response)
