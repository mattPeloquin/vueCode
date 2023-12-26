#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Code shared by AWS code
"""

from .. import log


def validate_response( response ):
    if response['ResponseMetadata']['HTTPStatusCode'] == 200:
        log.info2("AWS operation succeeded")
    else:
        log.error("AWS FAIL: %s", response)
