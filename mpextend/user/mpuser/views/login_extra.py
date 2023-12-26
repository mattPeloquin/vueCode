#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Simple views for extending login with extra information.

    These are EasyLink views that lookup information (sku, product, etc.)
    and pass along to login and portal extra.
    These views live here in portal because it made the code simpler
    and allowed for easier sharing.

    More complex setups for portal_extra, like GA, should be handled
    in the appropriate app.

    Many views support empty arguments not because they are a valid case,
    but to allow using {% url %} to pass a base url to JS for contcatonation.
"""
from urllib.parse import quote
from django.http import HttpResponseRedirect

from mpframework.common import log
from mpframework.user.mpuser.views.login import login_create
from mpframework.content.mpcontent.utils import content_search
from mpextend.product.catalog.models import PA
from mpextend.product.catalog.models import Coupon


def login_path( request, path=None ):
    """
    Support login to specific path on full site portal.
    """
    return _login_extra( request, 'path', path )

def login_sku( request, sku=None ):
    """
    Invite login that adds a license for the SKU to the user's account.
    """
    return _login_extra( request, 'sku', sku,
                _sku_extra_fn( request, sku ) )

def login_coupon( request, coupon_slug=None ):
    """
    Invite login that applies (general) coupon .
    """
    return _login_extra( request, 'coupon', coupon_slug,
                _coupon_extra_fn( request, coupon_slug ) )

def login_content( request, content_slug=None ):
    """
    Invite login to main portal with nav to content
    """
    return _login_extra( request, 'content', content_slug,
                _content_extra_fn( request, content_slug ) )


def login_portal_content( request, content_slug=None ):
    """
    Login redirect to content pages that are shown in their own tabs.
    """
    return _login_extra( request, 'content', content_slug,
                _content_extra_fn( request, content_slug ),
                **_portal_content_kwargs( content_slug ) )


def login_access( request, sku=None ):
    """
    Handle login from the access dialog, which always passes a SKU
    from user selection. Coupon is passed as querystring.
    """
    values, extra_fn = _access_setup( request, None, sku )
    return _login_extra( request, 'access', values, extra_fn )

def login_portal_content_access( request, content_slug, sku=None ):
    values, extra_fn = _access_setup( request, content_slug, sku )
    return _login_extra( request, 'access', values, extra_fn,
                **_portal_content_kwargs( content_slug ) )


def login_popup( request, content_slug=None ):
    """
    This view is shown in a popup window to support content iframes.
    Force simple login template and designate as a popup so successful
    logins cause the window to close.
    """
    request.is_popup = True
    return _login_extra( request, 'content', content_slug,
                _content_extra_fn( request, content_slug ),
                template='login_basic',
                **_portal_content_kwargs( content_slug ) )

def login_popup_access( request, content_slug, sku=None ):
    request.is_popup = True
    values, extra_fn = _access_setup( request, content_slug, sku )
    return _login_extra( request, 'access', values, extra_fn,
                template='login_basic',
                **_portal_content_kwargs( content_slug ) )

# Shared code for adding context info for login_extra. Structured as
# functions for lazy evaluation only if needed due to DB hit.

def _sku_extra_fn( request, sku ):
    def extra_fn():
        pa = PA.objects.pa_search( request.sandbox, sku )
        return {
            'pricing_option': pa,
            'sku': sku,
            'name': pa.name,
            'description': pa.description,
            }
    return extra_fn

def _coupon_extra_fn( request, coupon_slug ):
    def extra_fn():
        coupon = Coupon.objects.coupon_search( request.sandbox, coupon_slug )
        rv = {
            'coupon': coupon,
            'coupon_slug': coupon_slug,
            'description': coupon.description,
            }
        if coupon and coupon.pa:
            rv.update({
                'name': coupon.pa.name,
                })
        return rv
    return extra_fn

def _content_extra_fn( request, content_slug ):
    def extra_fn():
        content = content_search( request, content_slug )
        return {
            'content_item': content,
            'content_slug': content_slug,
            'name': content.name,
            'description': content.description,
            }
    return extra_fn

def _access_setup( request, content, sku ):
    coupon = request.GET.get('coupon')
    values = quote( '{},{}'.format( sku or '', coupon or '' ) )
    def extra_fn():
        rv = {}
        if content:
            rv.update( _content_extra_fn( request, content )() )
        if sku:
            rv.update( _sku_extra_fn( request, sku )() )
        if coupon:
            rv.update( _coupon_extra_fn( request, coupon )() )
        return rv
    return values, extra_fn

def _portal_content_kwargs( content_slug ):
    # Add extra args to keep portal content anchored
    return {
        'portal': 'portal_content_extra',
        'content_slug': content_slug,
        }

def _login_extra( request, ename, evalue, extra_fn=None, template=None, **kwargs ):
    """
    Shared functionality for passing along extra info to portal.
    """

    # Send straight to portal if logged in
    if request.user and request.user.is_authenticated:
        log.debug("Redirecting %s login to portal: %s -> %s",
                    ename, request.mpname, evalue)
        return HttpResponseRedirect(
                    request.sandbox.portal_url( ename, evalue, **kwargs ) )

    extra = {}
    if evalue:
        try:
            if extra_fn:
                extra.update( extra_fn() )
            extra.update({
                'portal_extra': kwargs,
                })
            extra['portal_extra'].update({
                'ename': ename, 'evalue': evalue,
                })
            log.debug("Login extra: %s -> %s", request.mpname, extra)
        except Exception as e:
            log.info2("SUSPECT - extra login failed %s: %s, %s -> %s",
                        request.mpipname, ename, evalue, e)

    return login_create( request, login_extra=extra, template=template )
