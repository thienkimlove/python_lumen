from django.conf.urls import url
from django.urls import path

from core.views import *

urlpatterns = [
    url(r'test', test, name='test'),
]