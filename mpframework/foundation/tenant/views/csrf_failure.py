#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Provide logging for Django CSRF failures
"""
from django.conf import settings
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.api import respond_api_expired


def handle_csrf_failure( request, reason="" ):
    """
    Apart from attacks, CSRF failures shouldn't happen in normal situations,
    but can happen if the browser cookies get out of whack.
    """
    log.warning_quiet("SUSPECT CSRF_FAIL %s - %s %s, %s -> %s", reason,
                request.mpipname, request.path,
                request.META.get('HTTP_REFERER'), request.META.get('HTTP_HOST'))
    if log.debug_on():
        from django.middleware.csrf import _unmask_cipher_token
        cookie_token = request.META.get('CSRF_COOKIE')
        form_token = request.POST.get( 'csrfmiddlewaretoken', '' )
        if not form_token:
            form_token = request.META.get( settings.CSRF_HEADER_NAME, '' )
        log.debug("CSRF_FAIL: cookie: %s -> %s, form: %s -> %s",
                cookie_token, cookie_token and _unmask_cipher_token(cookie_token),
                form_token, form_token and _unmask_cipher_token(form_token) )
        log.debug("%s", request.META)

    if request.is_api:
        return respond_api_expired()

    return TemplateResponse( request, 'tenant/csrf_failure.html' )
