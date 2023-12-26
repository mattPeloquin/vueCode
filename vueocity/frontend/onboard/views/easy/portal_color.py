#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    TBD Portal color tool
"""
from django.conf import settings

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.view import staff_required


@staff_required
def easy_portal_color( request, portal_url=None ):
    pass
