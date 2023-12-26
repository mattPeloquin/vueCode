#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF filtered multiple select
"""
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple


class mpSelectMultiple( FilteredSelectMultiple ):
    """
    Override Django filtered select to provide for custom JS loading
    to change layout and support autoselect versions.
    """

    @property
    def media( self ):
        js = [
            'admin/js/core.js',
            'mpf-js/staff/mpSelectFilter.js',
            ]
        return forms.Media( js=js )
