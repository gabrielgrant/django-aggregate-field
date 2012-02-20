
from datetime import datetime

from django.db import models
from django.test import TestCase

from django.contrib.auth.models import User

from example_project.test_app.models import Session, Event


"""
To run:

rm /tmp/aggregatefield.db
python manage.py syncdb  --noinput
python manage.py test aggregate_fields

For interactive tinkering:

python manage.py shell

class C(object): pass
self = C()

"""

class AggregateFieldTests(TestCase):
    def setUp(self):
        self.now = datetime.now()
        self.u = User.objects.create_user(username='name', email='em@il.com', password='pass')
        self.s = Session.objects.create(user=self.u)
        self.e = Event.objects.create(time=self.now, session=self.s)
    def test_in_filter(self):
        self.assertEqual(Session.objects.filter(start=self.now).count(), 1)
    def test_as_property(self):
        self.assertEqual(self.s.start, self.now)
    def test_fwd_lookup_chaining(self):
        pretty = Event.objects.filter(session__start=self.now)
        bleh = Event.objects.annotate(start=models.Min('session__events__time')).filter(start=self.now)
        self.assertListEqual(list(pretty), list(bleh))
    def test_backwards_lookup_chaining(self):
        pretty = User.objects.filter(sessions__start=self.now)
        bleh = User.objects.annotate(start=models.Min('sessions__events__time')).filter(start=self.now)
        self.assertListEqual(list(pretty), list(bleh))
    def test_object_chaining(self):
        bleh = self.u.sessions.all().annotate(start=models.Min('events__time')).filter(start=self.now)
        pretty = self.u.sessions.filter(start=self.now)
        self.assertListEqual(list(pretty), list(bleh))
    def test_caching(self):
        pass

