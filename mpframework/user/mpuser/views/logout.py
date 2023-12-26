#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Logout support
"""
from django.http import HttpResponseRedirect

from ..utils.login import logout_user


def logout( request, **kwargs ):
    """
    Log user out directly, and then redirect back to the referring page
    """
    user = request.user

    if user and user.is_authenticated:
        user.save()

    logout_user( request )

    next_page = request.referrer or request.sandbox.portal_url()

    return HttpResponseRedirect( next_page )
