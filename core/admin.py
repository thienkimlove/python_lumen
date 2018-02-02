from django.contrib import admin

# Register your models here.
from .models import *


class LogAdmin(admin.ModelAdmin):
    fields = ['link', 'agent', 'allow', 'country', 'response', 'sent']

admin.site.register(Log, LogAdmin)
