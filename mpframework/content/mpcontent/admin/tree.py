#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tree base admin, adds support for MPTT display

    # FUTURE - when new Django orderable field available (#25790), use to disable sorting
"""
from copy import deepcopy
from django import forms
from django.conf import settings
from django.urls import reverse
from django.utils.html import format_html
from mptt.admin import DraggableMPTTAdmin
from mptt.admin import JS

from mpframework.common import _
from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.utils import json_dump
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.frontend.sitebuilder.models import TemplateCustom
from mpframework.frontend.sitebuilder.admin.content_mixin import ContentOptionMixin

from ..cache import invalidate_group_content_timewin_provider
from ..models import Tree
from ..models import PortalType
from ..models import PortalGroup
from ..models import PortalCategory
from .tree_item import TreeItemAdminInline
from . import BaseItemAdmin
from . import BaseItemForm


class TreeForm( BaseItemForm ):
    """
    Include BaseItem form to get items shared with tree
    Items not shared with Tree will be ignored
    """
    class Meta:
        model = Tree
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            'parent': "Move into collection",
            '_items_tags': "Automatically add content",
            'panel': "Page layout",
            'viewer': "Content viewer",
            'nav_template': "Nav display",
            'node_template': "Children display",
            'item_template': "Items display",
            'background_image': "Background image",
            'image3': "Hero image",
            'image4': "Sidebar image",
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            'background_image': "bg_image",
            'image3': "image3",
            'image4': "image4",
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            'parent': "Make this top-level collection a child of a different "
                    "top-level collection.",
            '_items_tags': "Content items matching these license tags are added to "
                    "core items when saved (both existing and future).<br>"
                    "Items are not removed if this is modified.",
            'panel': "Override theme page layout template for this collection.",
            'viewer': "Override theme viewer template for this collection's content.",
            'nav_template': "Override theme nav element template to change "
                    "how links to this collection are displayed.",
            'node_template': "Override theme child node display template for this "
                    "collection and children.",
            'item_template': "Override theme item display template for this "
                    "collection's content items.",
            'workflow': "Set workflow visibility for the collection<br><br>"
                    "<div id='collection_set_workflow' class='mp_button'"
                            "style='width: 12em'>"
                    "Force item workflow</div><p class='mp_help_staff'>"
                    "Force collection content to match the workflow above.<br>"
                    "WARNING - items shared with other collections could<br>"
                    "have their workflow overwritten.</p>",
            'sandboxes': "Select sites for this collection<br><br>"
                    "<div id='collection_set_sandboxes'"
                        "class='mp_button' style='width: 12em'>"
                    "Force item sites</div><p class='mp_help_staff'>"
                    "Force collection content to match the sites above.<br>"
                    "WARNING - items shared with other collections could "
                    "have their sites overwritten.</p>",
            'background_image': "Optional image displayed as background for screens "
                    "showing this collection's content.",
            'image1': "Main image used with nav display cards and optionally as a hero "
                    "image if no separate hero image is provided.<br>"
                    "(location depends on the theme layout)",
            'image3': "Optional hero image used with top banners<br>"
                    "(location depends on the theme layout)",
            'image4': "Optional image used for a side or bottom banner<br>"
                    "(location depends on the theme layout)",
            # HACK - place root-visible button on form
            '_provider': "<div id='collection_rebuild' class='mp_button'>"
                         "Rebuild this tree (only top collections)</div><br>",
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            'text1': forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
            })

    yaml_form_fields = BaseItemForm.yaml_form_fields.copy()
    yaml_form_fields['sb_options']['form_fields'].extend([
            ] + ContentOptionMixin.yaml_form_fields_extensions )

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        if self.fields.get('panel'):
            self.fields['panel'].empty_label = u"Use default"
        if self.fields.get('viewer'):
            self.fields['viewer'].empty_label = u"Use default"
        if self.fields.get('nav_template'):
            self.fields['nav_template'].empty_label = u"Use default"
        if self.fields.get('node_template'):
            self.fields['node_template'].empty_label = u"Use default"


class TreeAdminBase( DraggableMPTTAdmin, BaseItemAdmin ):
    """
    Add Setup support specific to Trees and MPTT models
    """
    form = TreeForm
    inlines = ( TreeItemAdminInline ,)

    # Increase list per page to increase chance large trees fit and dynamics
    # with hiding items look ok, but unlike mptt, add limit for large sites
    list_per_page = BaseItemAdmin.list_per_page * 2

    # Force ordering to MPTT default
    ordering = ( 'mptt_id', 'mptt_left' )

    # Setup fields to use MPTT draggable
    list_display = ( 'list_actions', 'mptt_name', 'tag', 'workflow',
            'active_sandboxes', 'portal_type', 'portal_group',
            '_slug', 'internal_tags' )
    list_display_links = ( 'mptt_name' ,)
    list_text_small = BaseItemAdmin.list_text_small + (
            '_slug', )
    list_hide_small = BaseItemAdmin.list_hide_small + (
            '_slug', )

    # Narrow choices
    filter_mtm = dict( BaseItemAdmin.filter_mtm, **{
        'portal_categories': ( PortalCategory.objects, 'SANDBOX', ('scope__in','BC') ),
        })
    filter_fk = dict( BaseItemAdmin.filter_fk, **{
        'portal_type': ( PortalType.objects, 'SANDBOX', ('scope__in','BC') ),
        'portal_group': ( PortalGroup.objects, 'SANDBOX', ('scope__in','BC') ),
        'panel': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                            ('template_type','Q') ),
        'viewer': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                            ('template_type','F') ),
        'nav_template': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                            ('template_type','N') ),
        'node_template': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                            ('template_type','R') ),
        })

    # Allow MPTT fields to be displayed (may only be readonly)
    readonly_fields = BaseItemAdmin.readonly_fields + (
                        'parent_id', 'mptt_id', 'mptt_level', 'mptt_left', 'mptt_right' )

    # Rearrange the item fieldsets and setup for tree additions
    fs_content = 1
    fs_custom = 2
    fs_options = 3
    fs_html = 4
    fs_layout = 5
    fs_advanced = 6
    fs_root = 7
    fieldsets = [
        deepcopy( BaseItemAdmin.fieldsets[ BaseItemAdmin.fs_top ] ),
        (_("Content items"), {
            'classes': ('mp_collapse mp_placeholder tree_bi_items-group',),
            'fields' : [],
            }),
        deepcopy( BaseItemAdmin.fieldsets[ BaseItemAdmin.fs_custom ] ),
        deepcopy( BaseItemAdmin.fieldsets[ BaseItemAdmin.fs_options ] ),
        deepcopy( BaseItemAdmin.fieldsets[ BaseItemAdmin.fs_html ] ),
        (_("Layout"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                ] + ContentOptionMixin.fieldset_collection + \
                    ContentOptionMixin.fieldset_item,
            }),
        deepcopy( BaseItemAdmin.fieldsets[ BaseItemAdmin.fs_advanced ] ),
        deepcopy( BaseItemAdmin.fieldsets[ BaseItemAdmin.fs_root ] ),
        ]

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.ld_insert_pos = 4
        # Need to update filter_fk here to use the right manager
        self.filter_fk.update({
            'parent': ( self.model.objects, 'SANDBOX' ),
            })

    def formfield_for_foreignkey( self, db_field, request, **kwargs ):
        """
        Show only the top-level trees in parent
        """
        if db_field.name == 'parent':
            kwargs['queryset'] = Tree.objects.filter( parent_id__isnull=True )
            obj = request.mpstash.get('admin_obj')
            db_field.default = obj.pk if obj else None
        return super().formfield_for_foreignkey(
                                                db_field, request, **kwargs )

    def save_related( self, request, form, formsets, change ):
        """
        After any changes are made, need to update children
        """
        super().save_related( request, form, formsets, change )

        if change and form.instance:
            node = form.instance
            # First update this node, then do entire tree
            node.update_children()
            if not node.is_top:
                node.my_top.update_children()

    def changelist_view( self, request, *args, **kwargs ):
        """
        Override DraggableMPTTAdmin to point at MPF resources
        """

        # Execute the tree move
        if request.is_api and request.POST.get('cmd') == 'move_node':
            # Need to invalidate content timewins for the entire provider
            # because ordering of top collections defined in the timewin
            # bootstrap list
            invalidate_group_content_timewin_provider( request.sandbox.provider.pk )
            return self._move_node( request )

        response = super( BaseItemAdmin, self ).changelist_view( request, *args, **kwargs )

        # Override MPTT load js as needed, but not add css (loaded in staff css)
        try:
            response.context_data['media'] += forms.Media(
                js=[ JS( 'mpf-js/staff/mptt_draggable.js', {
                        'id': 'draggable-admin-context',
                        'data-context': json_dump( self._tree_context(request) ),
                        })
                    ],
                )
        except ( AttributeError, KeyError ) as e:
            log.debug("ADMIN error adding media:", e)

        return response

    def get_list_display( self, request ):
        """
        Modify changelist specific to collections
        """
        rv = list( super().get_list_display( request ) )
        if not request.user.access_high:
            rv.remove('_slug')

        # Nothing in the change lists can be sorted, as the order defines how the
        # trees are displayed and is modified with drag and drop
        self.list_display_not_sortable = rv

        return rv

    def get_fieldsets( self, request, obj=None ):
        """
        Remove baseitem fields not use with trees, and add
        tree and tree-top specific fields.
        """
        rv = super().get_fieldsets( request, obj )
        top = rv[ self.fs_top ][1]['fields']
        custom = rv[ self.fs_custom ][1]['fields']

        # Additions for all collections
        top[0] = ['_name', 'parent']

        if request.user.access_high:
            options = rv[ self.fs_options ][1]['fields']
            layout = rv[ self.fs_layout ][1]['fields']
            html = rv[ self.fs_html ][1]['fields']

            # Attributes for all collections
            options.insert( 3, ('_items_tags','portal__item_order'))
            custom.insert( 3, ('image4',) )
            layout.insert( 0, ('item_template','node_template') )
            layout.insert( 1, ('viewer','nav_template') )
            layout.insert( 2, ('portal__css_classes',) )
            html.append( 'html3' )

            # Attributes just for tops
            if obj and obj.is_top:
                custom[3] = ('image4','background_image')
                options.append(('portal__no_play_next','portal__hide_empty'))
                layout.insert( 0, ('image3','portal__hero_style') )
                layout.insert( 1, ('panel',) )

        return rv

    #-------------------------------------------------------------
    # MPTT Draggable overrides

    def mptt_name( self, item ):
        """
        Replace MPTT indented_title to provide nested display
        """
        return format_html( '<div style="text-indent:{}px">{}</div>',
                item._mpttfield('level') * self.mptt_level_indent, item.name )
    mptt_name.short_description = "Name"

    def list_actions( self, tree ):
        """
        Add tool and data for MPTT drag and drop, and edit nested
        """
        children = len( tree.get_descendant_ids )
        nest_msg = "edit {} children".format( children ) if children else "add children"
        nest_control = '' if not tree.is_top else format_html(
                '<a class="tree-children mp_button_flat" href="{}">{}</a>',
                    reverse( 'staff_admin:mpcontent_treenested_changelist_top',
                            kwargs={ 'top_id': tree.pk } ),
                    nest_msg,
                    )
        return format_html(
            '<div class="mp_flex_line">'
                '<div class="drag-handle"></div>'
                '{nest_control}'
                '<div class="tree-node" data-pk="{}"'
                    'data-tree="{}" data-level="{}" data-left="{}" data-right="{}"></div>'
                '</div>',
            tree.pk, tree._mpttfield('tree_id'), tree._mpttfield('level'),
            tree._mpttfield('left'), tree._mpttfield('right'),
            nest_control=nest_control
            )
    list_actions.short_description = ""

    def _tree_context( self, request ):
        return {
            'storageName': 'tree_collapsed',
            'treeStructure': self._build_tree_structure( self.get_queryset(request) ),
            'levelIndent': self.mptt_level_indent,
            'messages': {
                'before': "Move before item below",
                'child': "Make child of item above",
                'after': "Move after item above",
                'collapseTree': "Collapse",
                'expandTree': "Expand",
            },
        }

#--------------------------------------------------------------------

class TreeTopStaffAdmin( StaffAdminMixin, TreeAdminBase ):
    """
    Just the root tree nodes for top-level collection editing
    """

    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        qs = qs.filter( parent_id__isnull = True )
        return qs

class TreeTop( Tree ):
    class Meta:
        proxy = True
        verbose_name = u"Collection"

staff_admin.register( TreeTop, TreeTopStaffAdmin )


class TreeRootAdmin( TreeAdminBase ):
    """
    Show tree table as is, so all collections in mptt tree format.
    """
    list_display = TreeAdminBase.list_display + (
                        'parent_id', 'mptt_id', 'mptt_level', 'mptt_left', 'mptt_right')
    search_fields = TreeAdminBase.search_fields + ( '=parent__id', '=mptt_id', '=mptt_level' )

    def get_search_results( self, request, queryset, search_term ):
        """
        Force children to all show up as part of a search
        """
        qs, use_distinct = super().get_search_results(
                    request, queryset, search_term )
        child_ids = []
        for tree in qs.iterator():
            if tree.is_top:
                child_ids.extend( tree.get_descendant_ids )
        qs |= self.model.objects.filter( id__in=child_ids )
        return qs, use_distinct

    def formfield_for_foreignkey( self, db_field, request, **kwargs ):
        # Skip TreeAdminBase override to display everything in parent dropdown
        return super().formfield_for_foreignkey(
                                                db_field, request, **kwargs )
root_admin.register( Tree, TreeRootAdmin )
