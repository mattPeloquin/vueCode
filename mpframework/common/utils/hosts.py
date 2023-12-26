#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Host name utilities
"""
from django.conf import settings

from .. import log


_ignore_subdomains = [ '{}.'.format( subdomain ) for subdomain in
                        settings.MP_ROOT['HOST_SUBDOMAINS'] ]


def fixup_host_name( hostname ):
    """
    Do fixups to the hostname to support various dev and test scenarios,
    including running different server hosts against the same DB.
    """

    # HACK - Remove well-known sub-domains (e.g., 'mpd')
    for subdomain in _ignore_subdomains:
        if subdomain in hostname:
            hostname = hostname.replace( subdomain, '' )
            log.debug2("Hostname modified: %s -> %s", subdomain, hostname)
            break

    # In normal production, NO further checks to hostname
    if settings.MP_PROFILE_IS_PROD:
        return hostname

    # Non-WSGI cases need to account for local aliases
    host = _test_fixup( hostname )

    host = host.replace( '..', '.' )
    not settings.MP_TESTING and log.debug2("Hostname fixup: %s -> %s", hostname, host)
    return host

if settings.MP_WSGI:

    def _test_fixup( host ):
        return host

else:

    def _test_fixup( host ):
        for h in settings.MP_LOCALHOST_ALIASES:
            h = h.strip('.')
            if h in host:
                host = host.replace( h, '127.0.0.1' )
                break
        return host
