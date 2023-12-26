#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Return HTML for widgets to be incorporated in a page via javascript
"""

from mpframework.common.api import respond_api_call
from mpframework.common.utils.countries import COUNTRIES


#--------------------------------------------------------------------
# Country Selector

# Build HTML control from country list
country_options_html = ""
for code_and_name in COUNTRIES:
    country_options_html += "<option value='%s'>%s</option>" % code_and_name

def country_options( request ):
    """
    Returns info for country selection widget
    """
    def handler( _get ):
        return { 'country_options': country_options_html }

    return respond_api_call( request, handler, cache=True, methods=['GET'] )

