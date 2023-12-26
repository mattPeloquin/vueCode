#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    LMS content views
"""
from django.template.response import TemplateResponse

from mpframework.foundation.ops.csp import iframe_allow_any
from mpframework.content.mpcontent.delivery import cf_url
from mpframework.content.mpcontent.delivery import protected_access_cookie_response
from mpextend.content.mpcontent.models import LmsItem
from mpextend.user.usercontent.models import UserItem


@iframe_allow_any
def cookie_access_lms( request, no_host_id, access_key ):
    """
    Launch a SCORM package inside iframe with the SCORM API wrapper
    from the cloudfront URL.

    This allows LMS packages to run completely from a cloudfront URL, by
    placing the wrapper frame and SCORM frame under the same URL.
    """
    return protected_access_cookie_response( request, access_key,
                                             response_fn=_lms_response )

def _lms_response( request, session ):

    lms = LmsItem.objects.get( _provider_id=request.sandbox._provider_id,
                                id=session['data']['lms_id'] )

    return TemplateResponse( request, 'content/page/lms.html', {
            'is_page_content': True,
            'lms_url': cf_url( session, lms.package_url( session['data']['lms_version'] ) ),
            # Send what is needed to create a Backbone LMS item model
            'lms_item': lms,
            'cui': UserItem.objects.get_user_item( request.user, lms ),
            })
