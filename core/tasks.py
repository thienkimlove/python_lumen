# Create your tasks here
from __future__ import absolute_import, unicode_literals

import pycurl
import re
import redis

import sys
from celery import shared_task, task, group
from io import BytesIO

from celery.schedules import crontab
from celery.task import periodic_task
from strgen import StringGenerator

from core.models import Log, Agent


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


def virtual_curl(country, url, session, agent, redirection=0):
    username = 'lum-customer-theway_holdings-zone-nam-country-' + country
    password = '99oah6sz26i5'
    port = '22225'
    super_proxy = 'zproxy.luminati.io'
    url = url.replace("&amp;", "&")
    buffer = BytesIO()
    c = pycurl.Curl()
    c.setopt(pycurl.URL, url)
    c.setopt(pycurl.PROXY, 'http://' + super_proxy + ':' + port)

    c.setopt(pycurl.PROXYUSERPWD, username + '-session-' + session + ":" + password)

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
    except:
        type, value, tb = sys.exc_info()
        if hasattr(value, 'message'):
            result = "%s" % value.message
        else:
            result = 'Error'
    c.close()


    if redirection < 6:
        check = regex_check(result)
        if check is not None:
            redirection = redirection + 1
            return virtual_curl(country, check, agent, session, redirection)

    end_result = (result[:2000] + '..') if len(result) > 2000 else result

    return 'Source=' + end_result  + '|URL=' + url

#@task(ignore_result=True, serializer='pickle', compression='zlib')
def fetch_item(log_id):
    redis_client = redis.Redis()
    timeout = 60 * 60 * 5  # five hours
    lock = redis_client.lock(log_id, timeout=timeout)
    have_lock = lock.acquire(blocking=False)
    if have_lock:
        item = Log.objects.get(pk=log_id)
        session = StringGenerator('[a-z]{4}|[0-9]{4}').render()
        allow = 0 if item.allow > 4 else 1
        agent_row = Agent.objects.filter(type=allow).first()
        user_country = item.country.lower().replace(' ', ',')
        if ',' in user_country:
            user_country = user_country.split(',')[0]
        status = virtual_curl(user_country, item.link, session, agent_row.agent)
        try:
            item.agent = agent_row.agent
            item.response = status.encode('utf-8')
            item.sent = 1
            item.save()
        except:
            item.agent = agent_row.agent
            item.response = None
            item.sent = 1
            item.save()


#@task(ignore_result=True, serializer='pickle', compression='zlib')
def machine():
    logs = Log.objects.filter(sent__isnull=True).all()
    subtasks = group(fetch_item.s(log.id) for log in logs)
    subtasks.delay()
