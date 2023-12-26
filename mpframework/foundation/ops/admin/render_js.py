#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Monkey patch Django Media render_js to support
    deferred script loading.
"""
from django.forms.widgets import Media
from django.utils.html import format_html


def render_js( self ):
    return [
        format_html(
            '<script defer src="{}"></script>',
            self.absolute_path( path )
        ) for path in self._js
    ]

Media.render_js = render_js
