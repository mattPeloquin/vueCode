#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Ensure protected view handlers are imported
    Extended content urls are handled in extended content apps when needed.
"""
from django.urls import re_path

from . import api

# Load views event though not used to trigger response handler registration
from . import views


api_patterns_public = [

    # Override mpFramework item_access URL to add product and tracking
    re_path( r'^item_access$', api.item_access, name='api_item_access' ),

    ]
