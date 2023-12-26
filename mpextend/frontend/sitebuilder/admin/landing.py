#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Landing page admin
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.widgets import HtmlEditor
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.foundation.ops.admin import FieldChangeMixin

from ..models import LandingPage


class LandingPageForm( BaseModelForm ):
    class Meta:
        model = LandingPage
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'name': "Internal page name",
            'template': "HTML template",
            'inject_data': "Data for templates",
            })

        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'name': "Used to identify the page, not displayed to customer",
            'template': "Enter Vueocity template override.<br>"
                    "{help_templates}",
            'inject_data': "Add Content, Licensing, or custom items to template context.",
            })

        widgets = dict( BaseModelForm.Meta.widgets, **{
            'url': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'title': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'template': HtmlEditor( rows=32, protected=True ),
            'inject_data': CodeEditor( mode='yaml', rows=16 ),
            })

#--------------------------------------------------------------------

class LandingPageAdmin( FieldChangeMixin, BaseTenantAdmin ):

    form = LandingPageForm

    list_display = ( 'title', 'url', 'template', 'inject_data' )
    ordering = ( 'title' ,)

    list_filter = ( 'sandbox' ,)
    search_fields = ( 'title', 'url' )

    changed_fields_to_save = ( 'template' ,)

    fieldsets = [
        ('', {
            'classes': ('mp_collapse',),
            'fields': (
                'url',
                'title',
                'template',
                'inject_data',
                )
            }),
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'sandbox',
                ('hist_created', 'hist_modified'),
                )
            }),
        ]

root_admin.register( LandingPage, LandingPageAdmin )


class LandingPageStaffAdmin( StaffAdminMixin, LandingPageAdmin ):
    pass

staff_admin.register( LandingPage, LandingPageStaffAdmin )
