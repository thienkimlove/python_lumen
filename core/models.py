
from django.db import models

# Create your models here.
class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides selfupdating
    ``created`` and ``modified`` fields.
    """
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        abstract = True

class Agent(TimeStampedModel):
    id = models.AutoField(primary_key=True)
    agent = models.CharField(max_length=255, blank=True)
    type = models.PositiveSmallIntegerField(null=True)
    class Meta:
        db_table = 'agents'
    def __str__(self):
        return self.agent

class Log(models.Model):
    id = models.BigAutoField(primary_key=True)
    link = models.CharField(max_length=255, blank=True)
    allow = models.PositiveSmallIntegerField(null=True)
    country = models.CharField(max_length=255, blank=True)
    agent = models.CharField(max_length=255, blank=True)
    process = models.CharField(max_length=255, null=True)
    response = models.TextField(blank=True)
    sent = models.NullBooleanField()
    class Meta:
        db_table = 'logs'
    def __str__(self):
        return self.link
