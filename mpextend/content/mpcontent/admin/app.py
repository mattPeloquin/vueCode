#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Proxy app admin
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.widgets import CodeEditor
from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ..models import ProxyApp


class ProxyAppForm( BaseItemForm ):
    class Meta:
        model = ProxyApp
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            'proxy_main': "Source URL",
            '_proxy_options': "Advanced config",
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            'proxy_main': "The URL to access your web application",
            '_proxy_options': "Add advanced proxy options to fixup request or "
                "response from your web application. Headers or content can be "
                "modified globally and based on url regex matches.<br>"
                "{help_proxy_options}",
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            'proxy_main': forms.TextInput( attrs=mc.UI_TEXT_SIZE_LARGE ),
            '_proxy_options': CodeEditor( mode='yaml', rows=24 ),
            })


class ProxyAppAdmin( BaseItemAdmin ):
    form = ProxyAppForm

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )

        new_rows = [
            ( 'proxy_main' ,),
            ( '_proxy_options' ,),
            ]
        rv[ self.fs_content ][1]['fields'][0:0] = new_rows

        return rv

root_admin.register( ProxyApp, ProxyAppAdmin )


class ProxyAppStaffAdmin( StaffAdminMixin, ProxyAppAdmin ):
    pass

staff_admin.register( ProxyApp, ProxyAppStaffAdmin )
