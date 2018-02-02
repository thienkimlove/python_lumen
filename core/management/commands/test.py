import re

from bs4 import BeautifulSoup
import requests
from django.core.management import BaseCommand
from requests.packages.urllib3.exceptions import InsecureRequestWarning
from strgen import StringGenerator

from urllib.parse import urlparse, parse_qs


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

    credentials = 'lum-customer-theway_holdings-zone-nam-country-' + country + '-session-' + rand + ':99oah6sz26i5'

    url = url.replace("&amp;", "&")

    proxies = {
        "https": "https://" + credentials + "@zproxy.luminati.io:22225"
    }
    requests.packages.urllib3.disable_warnings(InsecureRequestWarning)
    session = requests.session()
    session.max_redirects = 10
    session.verify = False
    session.timeout = 60
    session.headers.update({'User-Agent': agent})
    session.proxies.update(proxies)

    try:
        g = session.get(url)
        g.raise_for_status()
        result = get_html_content(g.content)
    except requests.exceptions.Timeout as e:
        # Maybe set up for a retry, or continue in a retry loop
        result = "Error with request %s" % e
    except requests.exceptions.TooManyRedirects as e:
        # Tell the user their URL was bad and try a different one
        result = "Error with request %s" % e
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        result = "Error with request %s" % e
    print(result)

class Command(BaseCommand):
    help = 'Running virtual clicks'
    def handle(self, *args, **options):
        rand = StringGenerator('[a-z]{4}|[0-9]{4}').render()[::8]
        #url = 'https://www.whoishostingthis.com/tools/user-agent/'
        url = 'http://imnotbof.com/g/?q=LGbkZQc2pmb8BvWupUOsqKWfVwgmBwV8ZmbvnUE5pQbiY8AlqwHhoKyvMKA5MzIyMP0wo75ip8W7Y7AfnJAeYm4jnJD4ZwD6ZmR0AGNzpQR4LGV8ZGWvZGRgLJZkAF55MJD6YGtjZwLgAQR0MwL7MwHjAmIxWaNlCGpgAmtmBTZgKmMsMvMjAQ5zpQL4LGR0ZQuwMGZgZzV0Zl55BQD6YGt9MGRgAzR8MQIvAwIxBGIuWzAuMPH6DzEyqzywMI4cMzRyAHD4LGR0ZQuwMGZgZzV0Zl55BQD6YGt9MGRgAzR8MQIvAwIxBGIuWzAuMPH6DzqunJDyAHD4WzAuMPH6DzyxMzRyAHD4LGR0ZQuwMGZgZzV0Zl55BQD6YGt9MGRgAzR8MQIvAwIxBGIuVwgmBwR6BvW5pzSwn7yhM64xo76unJ9vB8Z1ZGV1Vzygoz45Lz4zYzAioFV2pmb5BvW6qJyxVwgmBwZ7BvWvAJWxZJEzAF55ZTZ0YGRkMGpgBTMvAF5jL7Z5A7R5ATEvLJRvB8Z1ZGN1VzAfnJAeK8I6nJDvB8Z1ZmL1VzRlAmRlLwRkYJSwZGHgATIxAF59ZQV7YGDkBJL7AzL6ZQp6MPV2pmb9BvWiMzMypy4cMPV2pmb6BvVlZGV8AlV2pmbkZQbvozI5q74ln64cMPV2pmb5BvVmAQZlVwgmBwR7BvWlMKAjo70mMI45rKOyK7yxVwgmBwV1VwR8VwgmBwR8BvWjqJWfnKAbMKWsqUyjMI4cMPV2nGb7B8Z1ZGV1VaO6Lzkcp7uypy4cMPV2nGbmBQZlB8Z1ZwbvqUZvB7D1ZGHkAmD9ZwV6BP97ZGNjZGx0B85%3D'
        country = 'gb'
        agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_0_2 like Mac OS X) AppleWebKit/601.1 (KHTML, like Gecko) CriOS/53.0.2785.109 Mobile/14A456 Safari/601.1.46'
        #proxy(url, country, agent, rand)
        self.stdout.write('done')
        #rexcheck
        content = "window.location = 'https://mobftrk.com/click?pid=12&offer_id=742187&sub1=P5P16R5174823478260495984&sub2=6051';"
        #print(regex_check(content))
        long_url = 'http://md.apptrknow.com/dir/click?placement_id=7828&campaign_id=26957816&affid=6202&cid=565637027ca5b45331a8b229c008559a_0_1517543897&data1=[data1]&data2=[data2]&data3=[data3]&data4=[data4]&affsub1=106&device_id=&idfa=&gaid=&uuid=7a8b5c16-1cad-4139-a118-58cb9676fdec&ref=apptrknow.com'
        try:
            requests.get(long_url)
        except UnicodeError as e:
            print("Error in proxy {}".format(e))
        o = urlparse(long_url)
        query = parse_qs(o.query)
        url = o._replace(query=None).geturl()
        print(url)
        print(query)
        print(requests.get(url, params=query))

        #encode = long_url.encode('idna')

