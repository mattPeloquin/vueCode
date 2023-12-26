#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Root admin for setting up SSO source
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import BaseModelAdmin

from ..models import SsoSource


class SsoSourceForm( BaseModelForm ):
    class Meta:
        model = SsoSource
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            })

class SsoSourceAdmin( BaseModelAdmin ):
    form = SsoSourceForm

    list_display = ( 'source_type', 'source_config' )
    list_display_links = ( 'source_type' ,)
    search_fields = ( 'source_type', 'source_config' )
    list_filter = ( 'source_type', 'hist_modified', 'hist_created' )

    ordering = ( 'source_type' ,)

    fieldsets = [
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'source_type',
                'source_config',
                )
            }),
        ]

root_admin.register( SsoSource, SsoSourceAdmin )
