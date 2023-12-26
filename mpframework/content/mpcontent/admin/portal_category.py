#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Category admin
"""
from copy import deepcopy

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin

from ..models import PortalCategory
from .base_attr import BaseAttrForm
from . import BaseAttrAdmin


class PortalCategoryForm( BaseAttrForm ):

    class Meta:
        model = PortalCategory
        exclude = ()

        labels = dict( BaseAttrForm.Meta.labels, **{
            'scope': "Use with",
            })
        labels_sb = dict( BaseAttrForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseAttrForm.Meta.help_texts, **{
            'scope': "Optionally limit type's usage to collections or items.",
            })
        widgets = dict( BaseAttrForm.Meta.widgets, **{
            })


class CategoryAdmin( BaseAttrAdmin ):
    form = PortalCategoryForm

    list_display = ( '_name', 'scope', 'workflow', 'active_sandboxes',
            'hist_modified', 'hist_created' )
    list_editable = BaseAttrAdmin.list_editable + ( 'scope' ,)

    fieldsets = deepcopy( BaseAttrAdmin.fieldsets )
    fieldsets[0][1]['fields'][0] = ('_name', 'scope')

root_admin.register( PortalCategory, CategoryAdmin )

class CategoryStaffAdmin( StaffAdminMixin, CategoryAdmin ):
    pass

staff_admin.register( PortalCategory, CategoryStaffAdmin )
