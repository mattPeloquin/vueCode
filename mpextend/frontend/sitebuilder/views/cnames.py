#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support management of external CNAMEs
"""

from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.view import staff_required


@staff_required( owner=True )
def manage_cnames( request ):

    # FUTURE - CNAME stuff

    request.is_page_staff = True
    return TemplateResponse( request, 'sitebuilder/cnames.html', {
                })
