#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin screens for content related models
"""
from copy import deepcopy
from django import forms

from mpframework.common import _
from mpframework.common import constants as mc
from mpframework.common.admin import root_admin
from mpframework.common.admin import mpListFilter
from mpframework.common.widgets import HtmlEditor
from mpframework.frontend.sitebuilder.models import TemplateCustom
from mpframework.frontend.sitebuilder.admin.content_mixin import ContentOptionMixin

from ..models import BaseItem
from ..models import Tree
from ..models import PortalType
from ..models import PortalGroup
from ..models import PortalCategory
from .base_attr import BaseAttrForm
from .base_attr import BaseAttrAdmin


class BaseItemForm( BaseAttrForm, ContentOptionMixin ):
    sanitize_html_fields = BaseAttrForm.sanitize_html_fields + (
            'tooltip', 'text3', 'text4' )
    class Meta:
        model = BaseItem
        exclude = ()

        labels = dict( BaseAttrForm.Meta.labels, **{
            'portal_type': "Portal type",
            'portal_group': "Portal group",
            'portal_categories': "Portal categories",
            'item_template': "Display template",
            'size': "Duration or size",
            '_points': "Point sizing",
            '_slug': "URL slug",
            '_available': "Available after",
            'text2': "Auxiliary text 2",
            'text3': "Auxiliary text 3",
            'text4': "Auxiliary text 4",
            'html1': "Portal HTML",
            'html2': "About HTML",
            'html3': "Protected viewing HTML",
            'tooltip': "Pop-up text",
            'search_tags': "Search keywords",
            '_action': "Access method",
            })
        labels_sb = dict( BaseAttrForm.Meta.labels_sb, **{
            'tag': "tag",
            'portal_type': "portal_type",
            'portal_group': "portal_group",
            'portal_categories': "portal_categories",
            '_slug': "slug",
            'tooltip': "tooltip",
            'text3': "text3",
            'text4': "text4",
            'html1': "html1",
            'html2': "html2",
            'html3': "html3",
            'search_tags': "search",
            'size': "size",
            '_points': "points",
            '_action': "action",
            })
        help_texts = dict( BaseAttrForm.Meta.help_texts, **{
            'tag': "Optional license tag for matching this content to one or "
                    "more pricing options (no spaces).<br>",
            'portal_type': "Optional custom type used to group and label "
                    "items in some theme layouts.",
            'portal_group': "Optional inclusion of content into a portal group, which "
                    "controls where the collection appears in the portal<br>",
            'portal_categories': "Optional categories for content filtering, grouping "
                    "and display.<br>"
                    "Only visible in some page layouts.",
            'item_template': "Override theme display template for this item.",
            'size': "Optional integer value for size or duration (e.g., minutes, hours, "
                    "pages, etc.). Is available for display in some templates and "
                    "can be totaled up for collections.",
            '_points': "Optional integer weighting the relative size of this item "
                    "for usage calculations (defaults to 1 if blank)",
            '_slug': "Customize the URL for the content (no spaces)<br>"
                        "SEO - URL is added to the sitemap for search indexing.",
            '_available': "Optionally set a date and time the content becomes visible "
                    "in Prod and Beta views. The content will be visible "
                    "and behave normally in Dev views.<br>"
                    "Leave blank for content to be available immediately.",
            'search_tags': "Keywords used for searches in the user portal. "
                    "Text in name and tags are included by default.",
            'internal_tags': "Optional tag(s) for admin search and management.<br>"
                    "Not shown to users and have no effect on display or licensing.",
            'tooltip': "Optional tooltip-style text displayed in popup.",
            'text3': "Optional text for use with some SiteBuilder templates.",
            'text4': "Optional text for usu with some SiteBuilder templates.",
            'html1': "Optional HTML used with some SiteBuilder templates to replace "
                    "how the item is displayed in the portal.",
            'html2': "Optional HTML used with some SiteBuilder templates to display "
                    "a tabbed or popup description.",
            'html3': "Optional HTML displayed alongside protected content "
                    "with some SiteBuilder viewer templates.",
            })
        widgets = dict( BaseAttrForm.Meta.widgets, **{
            'tag': forms.TextInput( attrs=mc.UI_TEXT_SIZE_CODE ),
            'portal_categories': forms.CheckboxSelectMultiple(),
            'tooltip': forms.Textarea( attrs={'rows': 2, 'cols': mc.CHAR_LEN_UI_DEFAULT} ),
            'html1': HtmlEditor( rows=16 ),
            'html2': HtmlEditor( rows=24 ),
            'html3': HtmlEditor( rows=24 ),
            'text3': forms.Textarea( attrs={'rows': 2, 'cols': mc.CHAR_LEN_UI_DEFAULT} ),
            'text4': forms.Textarea( attrs={'rows': 2, 'cols': mc.CHAR_LEN_UI_DEFAULT} ),
            'size': forms.NumberInput( attrs={'size': 6} ),
            '_points': forms.NumberInput( attrs={'size': 6} ),
            'search_tags': forms.Textarea( attrs={'rows': 2, 'cols': mc.CHAR_LEN_UI_DEFAULT } ),
            'internal_tags': forms.TextInput( attrs=mc.UI_TEXT_SIZE_CODE ),
            })

    # The action field must be explicitly defined because it is a CharField with
    # dynamically selected choices (so choices option is not set in model)
    _action = forms.ChoiceField( choices=BaseItem.ACTION_TYPICAL, required=False,
                help_text="Select how this content is delivered to users<br>"
                        "User experience may vary based on their browser settings." )

    portal__hide_if_no_access = forms.BooleanField( required=False,
            label="Hide if no access",
            help_text="Hide this content if the user does not have "
                    "access through an existing license or free offering." )
    portal__no_trials = forms.BooleanField( required=False,
            label="Never free / No trials",
            help_text="Prevent free or trial license access - content is visible "
                    "but only accessible when user has a non-trial license" )
    portal__coming_soon = forms.BooleanField( required=False,
            label="Coming soon",
            help_text="'Coming soon' items behave normally in Beta and Dev views. In "
                    "Prod access is prevented and special CSS styling is possible." )
    access__free_public = forms.BooleanField( required=False,
            label="Make free to public",
            help_text="Make this content accessible without a license for anyone, "
                    "including users not logged into your site." )
    access__free_user = forms.BooleanField( required=False,
            label="Make free to users",
            help_text="Make this content accessible without a license for "
                    "users logged into your site." )

    yaml_form_fields = BaseAttrForm.yaml_form_fields.copy()
    yaml_form_fields['sb_options']['form_fields'].extend([
            'portal__hide_if_no_access',
            'portal__no_trials', 'portal__coming_soon',
            'access__free_user', 'access__free_public',
            ])

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        if self.fields.get('item_template'):
            self.fields['item_template'].empty_label = u"Use default"


# Setup tenant-aware changelist filters
PortalTypeFilter = mpListFilter.new( PortalType,
        u"Portal type", 'portal_type_id' )
PortalGroupFilter = mpListFilter.new( PortalGroup,
        u"Portal group", 'portal_group_id' )
PortalCategoryFilter = mpListFilter.new( PortalCategory,
        u"Portal category", 'portal_categories__id' )


class BaseItemAdmin( BaseAttrAdmin ):
    """
    Shared behavior for admin of BaseItem types

    Sets up base item behavior for the Root admin screens.
    StaffAdminMixin will hide items that shouldn't appear in Provider admin
    """
    form = BaseItemForm

    LIST_START = ( '_name', 'tag', 'workflow' )
    LIST_END = ( '_tree', 'active_sandboxes',
            'portal_type', 'portal_group', 'internal_tags',
            'hist_modified', 'hist_created' )
    list_display = LIST_START + LIST_END
    list_editable = BaseAttrAdmin.list_editable + (
            'tag', 'portal_type', 'portal_group' )
    list_text_small = BaseAttrAdmin.list_text_small + (
            '_provider', '_sandbox', 'internal_tags',
            '_tree', 'portal_type', 'portal_group' )
    list_col_med = BaseAttrAdmin.list_col_med + (
            'portal_type', 'portal_group', 'internal_tags', )
    list_col_large = BaseAttrAdmin.list_col_large + (
            'tag', )
    list_hide_med = BaseAttrAdmin.list_hide_med + (
            'portal_group', 'internal_tags' )
    list_hide_small = BaseAttrAdmin.list_hide_small + (
            'portal_type', )

    list_filter = ( PortalTypeFilter, PortalGroupFilter, PortalCategoryFilter
            ) + BaseAttrAdmin.list_filter
    search_fields = BaseAttrAdmin.search_fields + (
            'tag', '_slug', 'internal_tags' )

    ordering = ( 'tag', '_name' )

    changed_fields_to_save = BaseAttrAdmin.changed_fields_to_save + (
            'tooltip', 'text3', 'text4', 'html1', 'html2', 'html3' )

    # Narrow choices
    filter_mtm = dict( BaseAttrAdmin.filter_mtm, **{
        'portal_categories': ( PortalCategory.objects, 'SANDBOX', ('scope__in','BI') ),
        })
    filter_fk = dict( BaseAttrAdmin.filter_fk, **{
        'portal_type': ( PortalType.objects, 'SANDBOX', ('scope__in','BI') ),
        'portal_group': ( PortalGroup.objects, 'SANDBOX', ('scope__in','BI') ),
        'item_template': ( TemplateCustom.objects, 'PROVIDER_OPTIONAL',
                            ('template_type','I') ),
        })

    # Update fieldsets from base by making a copy and modifying that,
    # and use standard offsets to adjust where sections live
    fs_content = 1
    fs_custom = 2
    fs_options = 3
    fs_html = 4
    fs_layout = 5
    fs_advanced = 6
    fs_root = 7
    fieldsets = deepcopy( BaseAttrAdmin.fieldsets )

    fieldsets.insert( fs_content,
        (_("Protected content"), {
            'classes': ('mp_collapse',),
            'fields': [],
            }))
    fieldsets.insert( fs_options,
        (_("Options"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                ('search_tags','_points'),
                ('portal_type', 'portal_group'),
                'portal_categories',
                ('_available','internal_tags'),
                ('portal__coming_soon','portal__no_trials'),
                ('portal__user_level','portal__hide_if_no_access'),
                ('access__free_user','access__free_public'),
                ],
            }))
    fieldsets.insert( fs_html,
        (_("HTML blocks"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                'html1',
                'html2',
                ],
            }))
    fieldsets.insert( fs_layout,
        (_("Layout"), {
            'mp_staff_level': 'access_high',
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                ('item_template','portal__css_classes'),
                ] + ContentOptionMixin.fieldset_item,
            }))

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        self.ld_insert_pos = 3

    def has_add_permission( self, request ):
        # Enforce policy limits
        can_add = super().has_add_permission( request )
        if can_add:
            can_add = self.model.objects.limits_ok(
                        _provider=request.sandbox.provider )
        return can_add

    def save_model( self, request, obj, form, change ):
        # Note if content has changed
        if not change or any([ field in form.changed_data for
                    field in obj.content_fields ]):
            obj.content_rev += 1
        super().save_model( request, obj, form, change )

    def formfield_for_manytomany( self, db_field, request, **kwargs ):
        # Remove retired categories
        if db_field.name == 'portal_categories':
            kwargs['queryset'] = PortalCategory.objects.exclude( workflow__in='R' )
        return super().formfield_for_manytomany(
                                                db_field, request, **kwargs )

    def get_list_display( self, request ):
        rv = list( super().get_list_display( request ) )
        if not request.user.access_high:
            '_tree' in rv and rv.remove('_tree')
            'portal_group' in rv and rv.remove('portal_group')
            'portal_type' in rv and rv.remove('portal_type')
            'internal_tags' in rv and rv.remove('internal_tags')
        return rv

    def get_list_filter( self, request ):
        rv = super().get_list_filter( request )
        user = request.user
        if user.access_high:
            rv = ( PortalTypeFilter ,) + tuple( rv )
        return rv

    def get_fieldsets( self, request, obj=None ):
        rv = super().get_fieldsets( request, obj )
        user = request.user
        top = rv[ self.fs_top ][1]['fields']
        custom = rv[ self.fs_custom ][1]['fields']
        advanced = rv[ self.fs_advanced ][1]['fields']

        top.insert( 1, ('tag',) )  # Space to add Slug
        if user.access_high:
            top[1] += ('_slug',)

        if user.access_med:
            custom.insert( 2, ('tooltip','size') )
            custom.insert( 3, ('text3','text4') )

        if user.access_all:
            advanced.insert( 0, ('_action',) )

        # Assume root is the last fieldset
        if user.access_root_menu:
            rv[ -1 ][1]['fields'].append((
                '_django_ctype',
                'content_rev',
                ))

        return rv

    def _tree( self, obj ):
        # FUTURE - if grabbing tree items on a per-tree basis is a performance
        # issue, do one grab for all trees on the current page in get_queryset
        trees = Tree.objects.values_list( '_name', flat=True )\
                    .filter( tree_bi_items__item=obj.id )\
                    .exclude( workflow__in='R' )
        return ', '.join([ tree for tree in list(trees) ])
    _tree.short_description = "Collections"
    _tree.admin_order_field = '_tree'


class BaseItemRootAdmin( BaseItemAdmin ):
    """
    Root admin includes collections in base item list and allows
    access to just the baseitem record
    """
    list_display = BaseItemAdmin.LIST_START + ( '_django_ctype' ,) + BaseItemAdmin.LIST_END
    list_filter = ( '_provider', '_django_ctype' ,) + BaseItemAdmin.list_filter

    search_fields = ( '_provider__name', 'text1' ,) + BaseItemAdmin.search_fields

root_admin.register( BaseItem, BaseItemRootAdmin )
