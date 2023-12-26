#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    URLs for supporting HTML editors
"""
from django.template.response import TemplateResponse

from mpframework.foundation.ops.csp import iframe_allow_site


@iframe_allow_site
def html_editor_frame( request ):
    """
    Load the iframe content for the editor; will be populated via javascript
    """
    return TemplateResponse( request, 'admin/html_editor_frame.html', {
                })
