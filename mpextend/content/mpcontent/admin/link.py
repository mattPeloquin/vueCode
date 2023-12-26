#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Proxy link admin
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.widgets import CodeEditor
from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ..models import ProxyLink


class ProxyLinkForm( BaseItemForm ):
    class Meta:
        model = ProxyLink
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            'link_type': "Link type",
            'proxy_main': "Link to share",
            'username': "Optional username",
            'password': "Optional password",
            '_proxy_options': "Advanced options",
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            'proxy_main': "Paste your shared link here",
            'username': "Some link types require a username",
            'password': "Some link types require a password",
            'link_type': "Select the type of link",
            '_proxy_options': "Add options to fixup request or response.<br>"
                    "{help_proxy_options}",
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            'proxy_main': forms.TextInput( attrs=mc.UI_TEXT_SIZE_LARGE ),
            '_proxy_options': CodeEditor( mode='yaml', rows=16 ),
            })

class ProxyLinkAdmin( BaseItemAdmin ):
    form = ProxyLinkForm

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )
        user = request.user

        new_rows = [
            ('proxy_main',),
            ('link_type',),
            ('username','password'),
            ]
        if user.access_all:
            new_rows.append( ('_proxy_options',) )

        rv[ self.fs_content ][1]['fields'][0:0] = new_rows
        return rv


root_admin.register( ProxyLink, ProxyLinkAdmin )


class ProxyLinkStaffAdmin( StaffAdminMixin, ProxyLinkAdmin ):
    pass

staff_admin.register( ProxyLink, ProxyLinkStaffAdmin )
