#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    LMS content views
"""
from django.conf import settings
from django.urls import reverse
from django.http import HttpResponseRedirect

from mpframework.common import log
from mpframework.common.utils import join_urls
from mpframework.content.mpcontent.delivery import cf_url
from mpframework.content.mpcontent.delivery import cf_signed
from mpframework.content.mpcontent.delivery import create_access_url
from mpframework.content.mpcontent.delivery import set_access_request_handler
from mpframework.content.mpcontent.delivery import set_access_response_handler

from ..models import LmsItem


def _lms_request_handler( item_id, **kwargs ):
    """
    Setup the lms session request with url information that will be
    cached so can be accessed after possible redirect through CF
    """
    data = {
        'lms_id': item_id,
        'lms_version': kwargs.get('version'),
        }
    return data, ''

set_access_request_handler( LmsItem.access_type, _lms_request_handler )


def _lms_response_handler( request, session ):
    """
    The protected content response for the access session will either redirect to the
    LMS package entry point, or redirect to an LMS frame through edge server
    that will then load the LMS package.
    """
    log.debug("PROTECTED LMS response: %s", session)

    # Redirect launch session to CF
    if cf_signed( request, session ):
        url = reverse( 'cookie_access_lms', kwargs={
                    'no_host_id': request.sandbox.pk,
                    'access_key': session['key'],
                    })
        url = cf_url( session, url )
        log.debug("LMS CF access url: %s", url)

    # Otherwise redirect straight to the launch url
    else:
        lms = LmsItem.objects.get( _provider_id=request.sandbox._provider_id,
                    id=session['data']['lms_id'] )
        url = lms.package_url( session['data']['lms_version'] )
        if settings.MP_CLOUD:
            url = create_access_url( request, 'download', url,
                        key=session['key'],
                        url_prefix=settings.MP_URL_PROTECTED_PASS,
                        default_mode=session['delivery_mode'] )
        else:
            log.info("DIRECT SERVE LMS PROTECTED: %s ", url)
            url = join_urls( settings.MP_URL_PROTECTED_XACCEL, url )

    return HttpResponseRedirect( url )

set_access_response_handler( LmsItem.access_type, _lms_response_handler )

