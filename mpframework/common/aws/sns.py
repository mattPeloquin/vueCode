#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    SNS interface
"""
from django.conf import settings

from .. import log
from . import get_resource


def get_sns():
    return get_resource('sns')

# TBD - SNS interface for SMS and PubSub service group task support
