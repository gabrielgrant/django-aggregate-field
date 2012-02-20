from django.db import models

class AggregateField(object):
    """
    Provides a quasi-field allowing direct referencing of aggregates
    """
    def __init__(self, aggregate_class, lookup, cache=False):
        self.aggregate = aggregate_class
        self.lookup = lookup
        self.cache = cache
        super(AggregateField, self).__init__()

    def contribute_to_class(self, cls, name):
        self.name = name
        self.attname = name
        self.model = cls
        cls._meta.add_virtual_field(self)
        # Connect myself as the descriptor for this field
        setattr(cls, name, self)

    def preprocess_query(self, i, parts, query):
        name = '__'.join(parts[:i] + [self.name])
        lookup = '__'.join(parts[:i] + [self.lookup])
        kwargs = {name: self.aggregate(lookup)}
        return parts[i], query.annotate(**kwargs)

    # descriptor methods
    def __get__(self, instance, owner):
        if instance is None:
            return self
        if self.cache and hasattr(self, 'value'):
            return self.value
        qs = self.model.objects.filter(pk=instance.pk)
        kwargs = {self.name: self.aggregate(self.lookup)}
        val = qs.aggregate(**kwargs)[self.name]
        if self.cache:
            self.value = val
        return val
    def __set__(self, instance, value):
        """
        Silently ignore setting a value

        This is needed, because if our value is set when doing
        reverse-joined lookups that point back at the object
        with the aggregate field defined.

        for example, given the models:

            class Event(models.Model):
                time = models.DateTimeField()
                session = models.ForeignKey('Session', related_name='events', null=True)

            class Session(models.Model):
                user = models.ForeignKey(User, related_name='sessions', null=True)
                start = AggregateField(models.Min, 'events__time')

        the query:

            user.sessions.filter(start=self.now)

        is equivalent to:

            user.sessions.all().annotate(start=models.Min('events__time')).filter(start=self.now)

        that is, it annotates the returned session with start times,
        which, when reconstituting the session objects, attempts to
        set the value on the "start" field. If setting the field raises
        an error, it is silently swallowed by Django (!) and an empty
        queryset is returned instead.
        """
        #raise AttributeError("can't set attribute")
        if self.cache:
            self.value = value
    def __delete__(self, instance):
        if self.cache:
            if hasattr(self, 'value'):
                del self.value
        else:
            raise AttributeError("can't delete attribute")

