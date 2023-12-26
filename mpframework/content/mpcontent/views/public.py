#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Public views related to content
"""

from mpframework.common.deploy.nginx import accel_redirect_public
from mpframework.foundation.ops.csp import iframe_allow_any
from mpframework.foundation.tenant.views import render_style_page

from ..utils import content_search


@iframe_allow_any
def content_description( request, content_slug ):
    """
    Render a content's description HTML in it's own style page,
    without any MPF templates.
    """
    item = content_search( request, content_slug )
    return render_style_page( request, item.description )

@iframe_allow_any
def content_image( request, content_slug=None ):
    """
    Provides access to default current image for content.
    """
    item = content_search( request, content_slug )
    image_url = item.image2_url or item.image1_url
    return accel_redirect_public( image_url )
