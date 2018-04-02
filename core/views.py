
# Create your views here.
from strgen import StringGenerator

from django.http import JsonResponse, HttpResponse

from core.management.commands.basic import virtual_curl


def test(request):
    rand = StringGenerator('[a-z]{4}|[0-9]{4}').render()[::8]
    allow = int(request.GET['allow'])
    country = request.GET['country']
    link = request.GET['link']
    agent = 'Mozilla/5.0 (iPhone; CPU iPhone OS 10_1 like Mac OS X) AppleWebKit/602.2.14 (KHTML, like Gecko) Mobile/14B72' if allow > 4 else 'Mozilla/5.0 (Linux; Android 5.0.1; SAMSUNG SM-N920K Build/LRX22C) AppleWebKit/537.36 (KHTML, like Gecko) SamsungBrowser/3.4 Chrome/34.0.1847.118 Mobile Safari/537.36'

    response = virtual_curl(country, link, rand, agent)

    return HttpResponse(response)