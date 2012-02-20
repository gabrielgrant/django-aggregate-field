from django.db import models

from django.contrib.auth.models import User

from aggregate_field.fields import AggregateField

class Event(models.Model):
    time = models.DateTimeField()
    session = models.ForeignKey('Session', related_name='events', null=True)

class Session(models.Model):
    user = models.ForeignKey(User, related_name='sessions', null=True)
    start = AggregateField(models.Min, 'events__time')
    end = AggregateField(models.Max, 'events__time', cache=True)

