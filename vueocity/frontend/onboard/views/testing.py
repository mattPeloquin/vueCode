#--- Vueocity Platform, Copyright 2021 Vueocity, LLC
"""
    Test and debug Views
"""

from django.template.response import TemplateResponse


def mptest_onboard( request ):
    return TemplateResponse( request, 'root/test/onboard.html', {
                })
