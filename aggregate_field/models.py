from types import MethodType

from django.db import models
from django.db.models.fields import FieldDoesNotExist
from django.db.models.sql.constants import LOOKUP_SEP
from django.db.models.query import QuerySet
from django.utils.tree import Node

old_filter_or_exclude = QuerySet._filter_or_exclude
def wrapped_filter_or_exclude(self, negate, *args, **kwargs):
    q_object = models.Q(*args, **kwargs)
    processed_qs = preprocess_q_object(self, q_object)
    new_qs = old_filter_or_exclude(processed_qs, negate, q_object)
    return new_qs

# ATCHUNG! monkey patch ahead
QuerySet._filter_or_exclude = MethodType(wrapped_filter_or_exclude, None, QuerySet)


def preprocess_q_object(queryset, q_object):
    leaf_children = get_leaf_children(q_object)
    for child in leaf_children:
        if not child:
            continue
        lookup, value = child
        queryset = preprocess_lookup(queryset, lookup)
    return queryset

def preprocess_lookup(queryset, lookup):
    parts = lookup.split(LOOKUP_SEP)
    fields = []
    lookup_model = queryset.model
    for i, p in enumerate(parts):
        opts = lookup_model._meta
        try:
            field = opts.get_field(p)
        except FieldDoesNotExist:
            vfs = dict((vf.name, vf) for vf in opts.virtual_fields)
            field = vfs.get(p)
        if field:
            # if the model is a related FK, get the source field
            if hasattr(field, 'related'):
                field = field.related.field
            fields.append((i, field))
            try:
                lookup_model = field.rel.to
            except AttributeError:
                lookup_model = None
        if not field or not lookup_model:
            # is it a reverse related field?
            try:
                field_object, model, direct, m2m = opts.get_field_by_name(p)
            except FieldDoesNotExist:
                break
            if not hasattr(field_object, 'field'):
                # this isn't a related field
                break
            else:
                related_field = field_object
            lookup_model = related_field.model
            field = related_field.field
            fields.append((i, field))
    for i, field in fields:
        preprocess_query = getattr(field, 'preprocess_query', None)
        if callable(preprocess_query):
            parts[i], queryset = preprocess_query(i, parts, queryset)
    return queryset

def get_leaf_children(q_object):
    leaf_children = []
    for child in q_object.children:
        if isinstance(child, Node):
            leaf_children.extend(get_leaf_chilren(child))
        else:
            leaf_children.append(child)
    return leaf_children

