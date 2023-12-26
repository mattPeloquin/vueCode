#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    AWS Healthcheck response
"""
from random import randint
from iptools import IpRangeList
from django.conf import settings
from django.http import Http404
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.deploy.server import mp_shutdown

from ..models import HealthCheck


_INTERNAL_IPS = IpRangeList( *settings.MP_DEV_IPS )
VALID_USER_AGENTS = settings.MP_ROOT['SERVER_HEALTH_USER_AGENTS']


def health_ping( request ):
    """
    Ping from load balancer

    If 200 is returned the server is considered healthy -- there are
    situations such as the DB not being available where the server
    should be kept in group, but an error should be reported.

    Health checks are special-cased in middleware, so this request
    object does not have host or sandbox.
    """
    server = settings.MP_IP_PRIVATE
    log.info4("HealthCheck: %s -> %s", server, request.ip)

    # If this request did not come from ELB or approved IP address, ignore
    agent = request.META.get('HTTP_USER_AGENT')
    if not agent or not any([ ua in agent for ua in VALID_USER_AGENTS ]):
        if not request.ip in _INTERNAL_IPS:
            log.info2("SUSPECT HealthCheck: %s -> %s", server, request.ip)
            raise Http404

    status = 204 if mp_shutdown().started() else 200
    outcome = "Checking health...<br>"
    try:
        # Don't do a full check everytime
        value = randint( 1, 8 )
        if value > 7:
            outcome += "Doing full check...<br>"
            outcome += HealthCheck.ping( request.ip )
        else:
            outcome += "Did light check<br>"
    except Exception:
        log.exception("HEALTH PING - %s", server)
        outcome += "<br>Server has an issue, see logs"

    return TemplateResponse( request, 'root/ops/health_check.html',
                    status = status,
                    context = {
                        'ip': request.ip,
                        'outcome': outcome,
                         })
