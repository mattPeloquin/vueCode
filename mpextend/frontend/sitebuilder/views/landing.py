#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Views for landing pages
"""
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.template import mpTemplate

from ..models import LandingPage


def landing_page( request, landing_url=None ):
    """
    Landing page response, throw exception for 404 if not valid
    """
    page = LandingPage.objects.get( sandbox_id=request.sandbox.pk, url=landing_url )
    return TemplateResponse( request, mpTemplate( page.template ),
                page.context )
