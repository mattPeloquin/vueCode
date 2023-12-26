#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    View and API code shared across MPF
"""

from .decorators import ssl_required
from .decorators import login_required
from .decorators import staff_required
from .decorators import root_only

from .template_view import mpTemplateView
