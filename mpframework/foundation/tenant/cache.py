#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Get and cache sandbox for requests

    The sandbox for a given host is cached and attached to all
    request objects in middleware.
"""
from django.http import Http404

from mpframework.common import log
from mpframework.common.cache import cache_rv
from mpframework.common.utils.hosts import fixup_host_name

from .models.sandbox import Sandbox


def get_sandbox( request, hostname=None ):
    """
    Returns a cached sandbox object for the hostname
    Treats non-existent hosts as a 404
    """
    if not hostname:
        hostname = request.host
    host_ids = _get_sandbox_and_provider_ids( hostname )
    if host_ids:
        sandbox_id, provider_id = host_ids
        sandbox = Sandbox.objects.get_sandbox_from_id( sandbox_id, provider_id )
        if sandbox:
            return sandbox
        request.mperror = "SUSPECT BAD_SANDBOX"
    else:
        request.mperror = "SUSPECT NO_SANDBOX"
    raise Http404

@cache_rv( keyfn=lambda hostname: ( fixup_host_name( hostname ), '' ),
            buffered='local_small' )
def _get_sandbox_and_provider_ids( hostname ):
    """
    Try to get sandbox based on host xxx.root.com or no-host ID and
    return tuple of sandbox and provider ID.
    The IDs are then used get/cache a sandbox object.
    The sandbox object id is looked up and invalidated using the request host
    (and sometimes id), as that is the only information available.
    It is highly unlikely a hostname's mapping to sand/prov IDs would
    change to a different ID, so the caching of the IDs isn't invalidated.
    """
    sandbox = None
    try:
        sandbox = Sandbox.objects.get_sandbox_from_host( hostname )
    except Sandbox.DoesNotExist:
        log.debug("No sandbox for hostname: %s", hostname)
    if not sandbox:
        try:
            id = int( hostname )
            sandbox = Sandbox.objects.get( id=id )
        except Exception:
            log.debug2("No sandbox for id: %s", hostname)
    if sandbox:
        log.info2("SANDBOX from host: %s -> %s", hostname, sandbox)
        return sandbox.pk, sandbox._provider_id
