
#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Custom template admin

    FUTURE - complete idea of pushing from dev to production workflow
"""
from django import forms

from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.admin import StaffAdminMixin
from mpframework.common.admin import mpListFilter
from mpframework.common.widgets import CodeEditor
from mpframework.common.utils.strings import close_compare
from mpframework.foundation.ops.admin import FieldChangeMixin
from mpframework.foundation.tenant.models.sandbox import Sandbox
from mpframework.foundation.tenant.models.provider import Provider
from mpframework.foundation.tenant.admin import BaseTenantAdmin
from mpframework.foundation.tenant.admin import ProviderOptionalAdminMixin

from ..models.template import TemplateCustom


# Special subsets of template types
HIDDEN_TYPES = ( 'J', 'K' )
MENU_THEME_TYPES = ( 'A', 'B', 'C' )

# Provide several different views into template subsets by dynamically
# creating Admin classes with the name in the tuple
ADMIN_SUBSETS = (
    ( 'A', 'font', u"Theme font" ),
    ( 'DB', 'style', u"Theme style" ),
    ( 'C', 'color', u"Theme color" ),
    ( 'INQRTV', 'layout', u"Portal layout" ),
    ( 'ELUV', 'other', u"Non-portal layout" ),
    )

class TemplateCustomForm( BaseModelForm ):
    class Meta:
        model = TemplateCustom
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'name': "Template name",
            '_script_name': "Script name",
            'code_prod': "Code used for Prod and Beta",
            'code_dev': "Code used for Dev workflow",
            '_all_sandboxes': "Use for all sites",
            '_sandboxes': "Limit to specific sites",
            'template_type': "Template type",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'name': "Name displayed for this template and used as default script name",
            '_script_name': "Optional name for use in VuePortal options and "
                    "mp_include tags.<br>"
                    "Leave blank to use name.",
            'code_prod': "This provides a view of the current code for the template, "
                    "which is shown when in Prod or Beta workflow.",
            'code_dev': "Custom template code used with Dev workflow. Use to experiment "
                    "until code is read for Prod/Beta.",
            'template_type': "UI area this template is intended for",
            '_all_sandboxes': "Make this template apply to all sites.",
            '_sandboxes': "Select sites this template is available in.",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'name': forms.TextInput( attrs=mc.UI_TEXT_SIZE_CODE ),
            '_sandboxes': forms.CheckboxSelectMultiple(),
            'code_dev': CodeEditor( mode='django', rows=32 ),
            'code_prod': CodeEditor( mode='django', rows=32 ),
            'code_backup': CodeEditor( mode='django', rows=32 ),
            'orig_path': forms.TextInput( attrs={'size': mc.CHAR_LEN_UI_WIDE} ),
            })


class CustomTemplateFilter( mpListFilter ):
    """
    Separate out groups of custom templates
    """
    model = Provider
    title = "System vs. Custom"
    parameter_name = 'system_vs_custom'
    def lookups( self, _request, _model_admin ):
        return (
            ('SYSTEM', "System templates"),
            ('PROVIDER', "Custom templates"),
            )
    def queryset( self, request, qs ):
        if self.value() == 'SYSTEM':
            return qs.filter( provider_optional=None )
        if self.value() == 'PROVIDER':
            return qs.filter( provider_optional=request.sandbox.provider )

class SandboxFilter( mpListFilter ):
    title = "Sites"
    parameter_name = 'sandbox'
    def lookups( self, request, _admin ):
        sandboxes = request.sandbox.provider.my_sandboxes.all()
        return [ (sb.pk, str(sb)) for sb in sandboxes ]
    def queryset( self, request, qs ):
        if self.value():
            return qs.filter( _sandboxes__id=self.value() )

class TemplateTypeFilter( mpListFilter ):
    title = "Template type"
    parameter_name = 'template_type'
    def lookups( self, request, _admin ):
        values = TemplateCustom.TEMPLATE_CUSTOM
        if request.user.access_root:
            values += TemplateCustom.TEMPLATE_HIDDEN
        return values
    def queryset( self, request, qs ):
        if self.value():
            return qs.filter( template_type__in=self.value() )


class TemplateCustomAdmin( FieldChangeMixin, ProviderOptionalAdminMixin,
                BaseTenantAdmin ):
    form = TemplateCustomForm
    list_display = ( 'provider_item', 'name', 'template_type', 'notes',
            '_all_sandboxes', 'has_dev_code', 'staff_level', '_script_name' )
    list_display_links = ( 'name' ,)
    list_add_root = BaseTenantAdmin.list_add_root + ( 'has_prod_code' ,)
    list_text_small = BaseTenantAdmin.list_text_small + (
            'provider_item', '_all_sandboxes', 'has_dev_code',
            '_script_name', 'template_type', 'staff_level' )
    list_col_med = BaseTenantAdmin.list_col_med + (
            '_script_name', 'template_type', 'staff_level' )
    list_hide_med = BaseTenantAdmin.list_hide_small + (
            'staff_level', )
    list_hide_small = BaseTenantAdmin.list_hide_small + (
            '_script_name', )
    list_filter = ( CustomTemplateFilter, TemplateTypeFilter, SandboxFilter )
    search_fields = ( 'name', '_script_name', 'notes', 'code_prod' )

    ordering = ( '-provider_optional', 'template_type', 'staff_level', 'name' )

    # Define explicit read-only fields for system items to prevent CodeMirror
    # fields from being turned into read-only text fields
    readonly_fields_system = ( 'name', '_script_name', 'template_type', 'notes' )

    # Although changes to prod are saved in backup, still save dev updates to
    # field changes to allow new work to be recovered if needed
    changed_fields_to_save = ( 'code_dev' ,)

    filter_mtm = dict( BaseTenantAdmin.filter_mtm, **{
            '_sandboxes': ( Sandbox.objects, 'PROVIDER' ),
             })

    fieldsets = [
        ('', {
            'classes': ('mp_collapse',),
            'fields': [
                ('name', 'template_type'),
                ('notes', '_script_name'),
                ]
            }),
        ('Production version', {
            'classes': ('mp_collapse',),
            'fields': [
                'code_prod',
                ]
            }),
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'provider_optional',
                'orig_path',
                'staff_level',
                'code_backup',
                )
            }),
        ]

    fieldsets_edit = [
        ('Dev version', {
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                'code_dev',
                )
            }),
        ]

    @property
    def can_copy( self ):
        return True

    def save_model( self, request, obj, form, change ):
        """
        Manage prod code backup and only save if different so
        cases where orig_code is loaded are not saved.
        """
        if change:
            new_prod = form.cleaned_data.get('code_prod', '')
            if new_prod:
                # If prod code is from orig, don't save
                if close_compare( new_prod, obj.orig_code ):
                    obj.code_prod = ''
                # If code has changed, make backup
                else:
                    initial = form.initial.get('code_prod', '')
                    if initial and new_prod != initial:
                        obj.code_backup = initial
        super().save_model( request, obj, form, change )

    def get_fieldsets( self, request, obj=None ):
        """
        Adjust fields based on user privilege
        """
        user = request.user
        rv = super().get_fieldsets( request, obj )

        # Adjust sandbox/workflow based on what user can see
        if( not obj or ( not obj.is_system and user.sees_sandboxes ) or
                request.GET.get('mpf_admin_copy_request') or user.access_root ):
            rv[0][1]['fields'].append( ('_all_sandboxes', '_sandboxes') )

        # Add dev edit field if not a system object
        if not obj or ( not obj.is_system or user.access_root ):
            rv = rv + self.fieldsets_edit

        # Load system items from code if needed; don't fail can't be found
        if obj and not obj.code_prod and obj.orig_path:
            try:
                obj.code_prod = obj.orig_code
            except Exception:
                pass

        return rv

    def has_prod_code( self, obj ):
        return bool( obj.code_prod )
    has_prod_code.short_description = "Prod code"
    has_prod_code.boolean = True

    def has_dev_code( self, obj ):
        return bool( obj.code_dev )
    has_dev_code.short_description = "Dev code"
    has_dev_code.boolean = True

#--------------------------------------------------------------------
# Staff views of themes and non-themes

class TemplateStaffAdmin( StaffAdminMixin, TemplateCustomAdmin ):

    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        qs = qs.exclude( template_type__in=HIDDEN_TYPES )
        return qs

    def formfield_for_choice_field( self, db_field, request, **kwargs ):
        # Remove template choices user can't see
        if db_field.name == 'template_type':
            kwargs['choices'] = self.add_choices
        return super().formfield_for_choice_field(
                                                          db_field, request, **kwargs )

class TemplateCustomStaffAdmin( TemplateStaffAdmin ):
    add_choices = TemplateCustom.TEMPLATE_CUSTOM

    def get_queryset( self, request ):
        qs = super().get_queryset( request )
        qs = qs.filter( TemplateCustom.has_access_Q( request.user.staff_level ) )
        qs = qs.exclude( template_type__in=MENU_THEME_TYPES )
        return qs

staff_admin.register( TemplateCustom, TemplateCustomStaffAdmin )


def _template_admin_factory( types, name, title ):
    """
    Create admin pages for each template subset
    """
    choices = []
    for choice in TemplateCustom.TEMPLATE_ALL:
        if choice[0] in types:
            choices.append( choice )

    # Create admin proxy model dynamically (note need to set __module__)
    meta = type( 'Meta', (object,), { 'proxy': True , 'verbose_name': title } )
    klass = type( str(name), ( TemplateCustom ,), {
                    '__module__': getattr( TemplateCustom, '__module__' ),
                    'Meta': meta
                    })

    class _TemplateStaffAdmin( TemplateStaffAdmin ):
        list_filter = ()
        add_choices = choices

        def get_queryset( self, request ):
            qs = super().get_queryset( request )
            qs = qs.filter( TemplateCustom.has_access_Q( request.user.staff_level ),
                        template_type__in=types )
            return qs

        def get_list_display( self, request ):
            # Show the template type of more than one type
            rv = list( super().get_list_display( request ) )
            if not len(choices) > 1:
                rv.remove('template_type')
            return rv

    staff_admin.register( klass, _TemplateStaffAdmin )

# Register the theme admin classes
for subset in ADMIN_SUBSETS:
    _template_admin_factory( *subset )

#--------------------------------------------------------------------
# Root adds filter to detect prod modifications

class ModifiedFilter( mpListFilter ):
    model = Provider
    title = "Prod Modified"
    parameter_name = 'prod_mod'

    def lookups( self, _request, _model_admin ):
        return (
            ('MODIFIED', "Loading from DB"),
            ('ORIGINAL', "Loading from code"),
            )

    def queryset( self, request, qs ):
        if self.value() == 'MODIFIED':
            return qs.exclude( code_prod='' )
        if self.value() == 'ORIGINAL':
            return qs.filter( code_prod='' )

class TemplateCustomRootAdmin( TemplateCustomAdmin ):
    list_display = ( 'orig_path', 'provider_item', 'name', '_script_name',
            'has_prod_code', 'has_dev_code', '_all_sandboxes',
            'template_type', 'staff_level', 'notes' )
    list_editable = ( '_script_name', 'template_type', 'staff_level', 'notes' )
    list_text_small = TemplateCustomAdmin.list_text_small + (
            'orig_path', 'has_prod_code' )
    search_fields = ( 'name', '_script_name', 'orig_path' )
    list_filter = TemplateCustomAdmin.list_filter + (
            'staff_level', ModifiedFilter )
    list_per_page = 160

root_admin.register( TemplateCustom, TemplateCustomRootAdmin )
