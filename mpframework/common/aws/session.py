#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Thread-safe access to boto clients and resources

    All boto3 services have clients and some have higher level resource
    interfaces; MPF may use one or the other depending on need.

    Since threads could be created in different contexts, store the
    boto3 session lazily in thread local storage.
    For calls to AWS on remote servers, local credentials are used,
    while for calls on EC2 serves, use IAM roles.
"""
import boto3
from django.conf import settings

from .. import log
from ..deploy.server import get_thread_local


def get_resource( res_name ):
    session = get_thread_local( 'boto3_session', boto3.session.Session )

    def _get_resource():
        rv = session.resource( res_name, **_get_credentials() )
        assert rv
        if settings.MP_CLOUD:
            log.debug("New AWS boto3 resource(%s): %s", res_name, rv)
            return rv

    return get_thread_local( 'boto3_{}'.format( res_name ), _get_resource )

def get_client( client_name ):
    session = get_thread_local( 'boto3_session', boto3.session.Session )

    def _get_client():
        rv = session.client( client_name, **_get_credentials() )
        assert rv
        if settings.MP_CLOUD:
            log.debug("New AWS boto3 client(%s): %s", client_name, rv)
            return rv

    return get_thread_local( 'boto3_{}'.format( client_name ), _get_client )

def _get_credentials():
    """
    Get credentials either from local secrets (dev) or AWS.
    """
    rv = {
        'region_name': settings.MP_AWS_INSTANCE['region'],
        }

    # When running outside server profile (so can't use boto3 roles) get
    # credential information from secrets.
    # TBD SECURE - Add support for getting credentials in roles in boto calls
    # for now get from info for commands secrets
    if settings.MP_AWS_INSTANCE.get('outside_aws'):

        # HACK - try reading from local file on dev machine
        # TBD SECURE - ONLY used for 'fab a', remove when reworked
        from .secrets import _SECRETS
        rv.update({
            'aws_access_key_id': _SECRETS.get( 'access_key', '' ),
            'aws_secret_access_key': _SECRETS.get( 'access_secret', '' ),
            })

    return rv
