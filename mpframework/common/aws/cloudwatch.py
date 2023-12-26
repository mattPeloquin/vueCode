#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared Cloudwatch code
"""

from . import get_resource


def get_cloudwatch():
    return get_resource('cloudwatch')

# FUTURE - may use cloudwatch for key dashboard info for root
