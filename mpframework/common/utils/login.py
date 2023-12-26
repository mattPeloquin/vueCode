#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for redirecting to the login page.

    HACK - small amount of knowledge of user login URL here
"""
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import reverse

from .. import log
from ..api import respond_api
from ..utils.request import QUERYSTRING_PREFIX
from ..utils.http import append_querystring


def redirect_login( request ):
    """
    Redirect request to login, usually from an error/security violation
    """
    if settings.MP_TESTING:
        from mpframework.testing.framework import mpTestingException
        raise mpTestingException("Redirect to login: %s" % request.uri)

    log.info2("USER AUTH - LOGIN REDIRECT: %s from %s", request.mpipname, request.uri)
    login_url = reverse('login')
    qs = {}
    qs[ QUERYSTRING_PREFIX + 'signin' ] = 1
    login_url = append_querystring( login_url, **qs )
    return HttpResponseRedirect( login_url )


def authenticate_error_response( request ):
    """
    Standard handling for failure of user authorization
    """
    if request.is_api:
        log.info2("USER AUTH - AJAX: %s -> %s", request.mpipname, request.uri)
        return respond_api( False )
    else:
        return redirect_login( request )
