#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Handles Uploads outside of Django storages, and operations on S3
    like copying.

    Uploads outside of Django storages:
        - LMS package content uploads
        - Report csv uploads
"""
import mimetypes
from django.conf import settings
from boto3.s3.transfer import TransferConfig

from .. import log
from ..utils import join_urls
from ..utils.http import cache_control_dict
from ..utils.http import attachment_string
from ..utils.http import append_querystring
from . import get_resource


# May need to tune copy concurrency based on server and usage
_copy_config = TransferConfig( max_concurrency=2 )


def get_s3():
    return get_resource('s3')

def protected_bucket():
    if settings.MP_CLOUD:
        return get_s3().Bucket( settings.MP_AWS_BUCKET_PROTECTED )

def public_bucket():
    if settings.MP_CLOUD:
        return get_s3().Bucket( settings.MP_AWS_BUCKET_PUBLIC )


# Get cache control names that match browser strings and boto args
def cache_control_public():
    return cache_control_dict(
                        settings.MP_CACHE_AGE['BROWSER'],
                        settings.MP_CACHE_AGE['EDGE']
                        )['cache-control']
def cache_control_protected():
    return cache_control_dict(
                        settings.MP_CACHE_AGE['BROWSER_PROTECTED'],
                        settings.MP_CACHE_AGE['EDGE_PROTECTED']
                        )['cache-control']
_public_extra = {
    'CacheControl': cache_control_public()
    }
_protected_extra = {
    'CacheControl': cache_control_protected()
    }

def url_add_attachment( url, filename ):
    """
    Add the S3 querystring for setting attachment in content-disposition response.
    Browsers assume inline if not specified, so only set if attachment.
    """
    rv = url
    if filename:
        qs = { 'response-content-disposition': attachment_string( filename ) }
        rv = append_querystring( rv, **qs )
    return rv

def upload_public( filepath, s3key, extra=_public_extra ):
    if not settings.MP_CLOUD:
        return
    log.info3("S3 PUBLIC upload: %s -> %s", filepath, s3key)
    rv = None
    try:
        extra = _guess_type( filepath, extra )
        rv = public_bucket().upload_file( filepath, s3key, ExtraArgs=extra )
    except Exception:
        log.exception("S3 public upload: %s -> %s", filepath, s3key)
    return rv

def upload_protected( filepath, s3key, extra=_protected_extra ):
    if not settings.MP_CLOUD:
        return
    log.info3("S3 PROTECTED UPLOAD: %s -> %s", filepath, s3key)
    rv = None
    try:
        extra = _guess_type( filepath, extra )
        rv = protected_bucket().upload_file( filepath, s3key, ExtraArgs=extra )
    except Exception:
        log.exception("S3 protected upload: %s -> %s", filepath, s3key)
    return rv

def copy_file( bucket, source_key, dest_key ):
    """
    Copy a file within public or protected bucket
    """
    log.info3("S3 COPY %s: %s -> %s", bucket, source_key, dest_key)
    try:
        bucket = protected_bucket() if bucket == 'protected' else public_bucket()
        if not bucket:
            log.debug("Skipping copy_public, S3 bucket not available")
            return

        source = {
            'Bucket': bucket.name,
            'Key': source_key,
            }
        bucket.copy( source, dest_key, Config=_copy_config )

    except Exception:
        log.exception("S3 COPY %s: %s -> %s", bucket, source_key, dest_key)
        # FUTURE - if there are frequent problems with copy, implement queued retry


def _guess_type( filepath, extra ):
    """
    FUTURE - boto3 will detect mime type as option in future release
    """
    rv = extra
    if not 'ContentType' in extra:
        type = mimetypes.guess_type( filepath )[0]
        if type:
            rv = {}
            rv.update( extra )
            rv['ContentType'] = type
    return rv


# Largest number of granular keys that can be deleted at one time
DELETE_MAX = 500

def remove_folder_or_file( bucket, *args ):
    """
    Remove the given key from S3

    THIS WILL REMOVE ALL ITEMS UNDER A FOLDER
    This is intended for automated maintenance at a fine granularity,
    so there are some sanity checks

    If bucket is configured for versioning, this will just
    create delete markers, so items could be recovered.
    """

    # If any args do not have values, abort, as it could cause
    # unwanted folder deletion
    if not all( args ):
        log.error("S3 DELETE called with empty path arg: %s", args)
        return

    if bucket:
        key_prefix = join_urls( settings.MP_PLAYPEN, *args )
        keys_to_remove = [ key for key in bucket.list( prefix = key_prefix ) ]

        if len( keys_to_remove ) > DELETE_MAX:
            log.error("S3 DELETE called on too many keys")
            return

        if keys_to_remove:
            log.info("Removing %s keys from S3: %s", len( keys_to_remove ), keys_to_remove[:8])
            bucket.delete_keys( keys_to_remove )
            return True
