#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django Storages S3 extension

    Files uploaded through Django storages are processed here
"""
from django.conf import settings
from storages.backends.s3boto3 import S3Boto3Storage

from .. import log
from ..utils.http import cache_control_dict
from ..aws.secrets import aws_s3_credentials


def _cache_control_dict( browser=None, edge=None ):
    return cache_control_dict( browser, edge, name='CacheControl' )


class mpS3BotoStorage( S3Boto3Storage ):
    """
    Base class for MPF S3 storage that override some S3 boto behavior
    """

    # By default, set CacheControl to 0 (override in specializations)
    cache_age_browser = None
    cache_age_cf = None

    def __init__( self, *args, **kwargs ):
        """
        Setup parameters for content storage
        """

        # The normal default is to lock down items on S3,
        # all 'public' access is via cloudfront ONLY
        kwargs['default_acl'] = 'private'

        # Update S3 metadata headers
        s3_params = kwargs.get( 'object_parameters', {} )
        s3_params.update( _cache_control_dict(
                    self.cache_age_browser, self.cache_age_cf ))
        kwargs['object_parameters'] = s3_params

        key, secret = aws_s3_credentials()
        super().__init__(
                access_key=key,
                secret_key=secret,
                *args, **kwargs
                )

    def _save( self, name, content ):
        try:
            # Turn off caching for selected file extensions
            for ext in settings.MP_EDGE_NOCACHE:
                if name.endswith( ext ):
                    log.debug2("Setting NOCACHE: %s", name)
                    self.object_parameters = _cache_control_dict()
                    break

            return super()._save( name, content )
        except Exception:
            log.exception("\nProblem saving item to S3")

    def url( self, name ):
        raise Exception("Define access URL in specializations")
