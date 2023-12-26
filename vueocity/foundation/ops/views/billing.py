#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Views related to tenant management
"""

from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.view import staff_required

@staff_required( owner=True )
def owner_billing( request ):

    # FUTURE - billing stuff

    return TemplateResponse( request, 'owner/billing.html', {
                })
