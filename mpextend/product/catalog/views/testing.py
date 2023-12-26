#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Test and debug Views
"""

from django.template.response import TemplateResponse


#--------------------------------------------------------------------
# Provide basic test access to templates not accessible via url

def template_pa_success( request ):
    return TemplateResponse( request, 'payment/success.html', {
                })

