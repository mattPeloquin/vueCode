#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared Cloudfront code

    This code only interacts with CF to generate signed URLs;
    configuration of CF is done with TerraForm.
"""
import rsa
from botocore.signers import CloudFrontSigner
from django.conf import settings

from .. import log
from ..utils import timedelta_future


def cf_signer():
    """
    Cache creation of CloudFrontSigner.
    """
    global _cf_signer
    if not _cf_signer:
        key_id = settings.MP_ROOT_AWS['CF_KEY_ID']
        log.debug("Caching new CF signer: %s", key_id)

        key = rsa.PrivateKey.load_pkcs1( settings.MP_ROOT_AWS['CF_KEY'] )

        def rsa_signer( message ):
            # CF requires bytes and SHA-1; due to different paths through
            # CloudFrontSigner, message may have already been converted
            if not isinstance( message, bytes ):
                message = message.encode()
            return rsa.sign( message, key, 'SHA-1' )

        _cf_signer = CloudFrontSigner( key_id, rsa_signer )

    return _cf_signer
_cf_signer = None


def get_signed_url( url, seconds, ip=None ):
    """
    Returns a ready-to-go signed URL based on root CF setup, the folder
    associated with the URL, and seconds/ip options.
    """
    policy = _custom_policy( url, seconds )

    rv = cf_signer().generate_presigned_url( url, policy=policy )

    log.aws("Created CF signed url: %s, %s => %s", url, policy, rv)
    return rv

def get_signed_cookies( url, seconds, ip=None ):
    """
    Returns cookies for protected URL based on root CF and options.
    """
    signer = cf_signer()
    policy = _custom_policy( url, seconds )
    signature = signer.rsa_signer( policy )
    cookies = {
        'CloudFront-Policy': signer._url_b64encode( policy.encode() ).decode(),
        'CloudFront-Signature': signer._url_b64encode( signature ).decode(),
        'CloudFront-Key-Pair-Id': signer.key_id,
        }
    log.aws("Created CF signed cookies: %s, %s => %s", url, policy, cookies)
    return cookies


def _custom_policy( url, seconds ):
    expire = timedelta_future( seconds=seconds )
    return cf_signer().build_policy( url, expire )
