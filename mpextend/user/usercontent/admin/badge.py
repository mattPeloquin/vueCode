#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Badges admin
"""
from copy import deepcopy
from django import forms

from mpframework.common import _
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.content.mpcontent.admin import BaseFieldForm
from mpframework.content.mpcontent.admin import BaseFieldAdmin
from mpframework.content.mpcontent.tags import tag_code_help

from ..models import Badge


class BadgeForm( BaseFieldForm ):
    class Meta:
        model = Badge
        exclude = ()

        labels = dict( BaseFieldForm.Meta.labels, **{
            '_tag_matches': "Content matches",
            'completion': "Completion type",
            'certificate_file': "Upload certificate",
            'badge_tag': "Badge tag",
            })
        labels_sb = dict( BaseFieldForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseFieldForm.Meta.help_texts, **{
            '_tag_matches': tag_code_help(),
            'completion': "Select how this badge is earned for the selected content.",
            'certificate_file': "Optional upload of file for download "
                "upon completion",
            'badge_tag': "Optionally group badges and/or tie them to specific "
                "licenses.",
            })
        widgets = dict( BaseFieldForm.Meta.widgets, **{
            })

class BadgeAdmin( BaseFieldAdmin ):
    form = BadgeForm
    list_display = ( '_name', 'completion', 'hist_modified', 'hist_created' )
    list_filter = BaseFieldAdmin.list_filter + ('completion',)
    list_col_large = BaseFieldAdmin.list_col_large + ('completion',)
    ordering = ( '_name', 'completion' )

    fieldsets = deepcopy( BaseFieldAdmin.fieldsets )
    fieldsets[0] = (
        "", {
            'fields': [
                ('_name','badge_tag'),
                ('_tag_matches','completion'),
                ('text1','image1'),
                ]
            })

root_admin.register( Badge, BadgeAdmin )


class BadgeStaffAdmin( StaffAdminMixin, BadgeAdmin ):
    pass

staff_admin.register( Badge, BadgeStaffAdmin )
