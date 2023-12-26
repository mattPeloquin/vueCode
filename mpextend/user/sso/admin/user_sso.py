#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Root admin for sso user
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import BaseModelAdmin

from ..models import UserSSO


class UserSsoForm( BaseModelForm ):
    class Meta:
        model = UserSSO
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            })

class UserSsoAdmin( BaseModelAdmin ):
    form = UserSsoForm

    list_display = ( 'user', 'source' )
    list_display_links = ( 'user' ,)
    list_editable = ( 'source' ,)
    search_fields = ( 'user__email', 'source__source_type' )
    list_filter = ( 'source', 'hist_modified', 'hist_created' )

    readonly_fields = BaseModelAdmin.readonly_fields + ( 'user' ,)

    fieldsets = [
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'user',
                'source',
                )
            }),
        ]

root_admin.register( UserSSO, UserSsoAdmin )
