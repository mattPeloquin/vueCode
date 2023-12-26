#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Server proxy delivery

    Use the interface below to create a proxy session that will hold state
    across multiple calls to a proxy server. The requests/responses
    to/from the proxy can be fixed up through configuration options.
"""


def full_url( request, url, *path, **kwargs ):
    """
    Return full url from parts, with scheme prefix if not provided
    """
    from mpframework.common.utils import join_urls
    if not url.startswith('http'):
        url = '{}://{}'.format( request.scheme, url )
    return join_urls( url, *path, **kwargs )


from .response import default_fixups
from .session import proxy_access_session
from .call import get_proxy_response
