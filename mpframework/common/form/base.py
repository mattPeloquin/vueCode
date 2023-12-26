#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared forms code - for both admin and normal views

    Parsley support for forms is added here by running the
    standard parsleyfy against the form.
    "common/parsley.js" must be loaded for parsley fields to work.
"""
from django import forms
from django.conf import settings
from django.contrib.admin import widgets
from django.utils.safestring import mark_safe

from .. import log
from .. import constants as mc
from ..utils.strings import replace_text_tags
from ..widgets import mpSelect2
from ..widgets import mpSelectMultiple
from ..widgets import CodeEditor
from .parsley import parsleyfy


_MULT_CHOICE_THRESHOLD = settings.MP_UI_OPTIONS.get( 'MULT_CHOICE_THRESHOLD', 8 )


@parsleyfy
class BaseForm( forms.Form ):
    """
    Add parsley to base form for framework
    """

    # Force loading JS/CSS through framework
    class Media:
        js = ()
        css = {}

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        log.debug2("Form init: %s -> %s, %s", self.fields, args, kwargs)


@parsleyfy
class BaseModelForm( forms.ModelForm ):
    """
    Base for MPF model forms (not just BaseModel) - primarily Admin forms
      - Admin forms expect the mpf_request processing for user/sandbox
      - Adds parsley and shared model form behavior for staff UI screens
      - Text fields are bleached when posted by default
      - Adds shared admin behavior
      - Supports creating admin controls for one Yaml field (e.g., sb_options)
    """

    # Force loading JS/CSS through framework
    class Media:
        js = ()
        css = {}

    # Setups defaults that are consistent across many models
    class Meta:

        labels = {
            'notes': "Staff notes",
            }
        labels_sb = {
            }
        help_texts = {
            'notes': "Provide comments for staff; users never see this text",
            }
        widgets = {
            'notes': forms.Textarea(attrs=mc.UI_TEXTAREA_DEFAULT ),
            }

    # Setup autolookup fields for foreign keys
    autolookup_fields = ()

    # Support using yaml field elements on the admin form
    # Each model yaml field name is a key to a dict which holds
    # a list of form field names in 'form_names' and an
    # optional 'upstream_getter' to support overrides.
    yaml_form_fields = {}

    def __init__( self, *args, **kwargs ):

        # If request is available, stash the user and sandbox
        request = kwargs.pop('mpf_request', None)
        self.user = request.user if request else None
        self.sandbox = request.sandbox if request else None

        super().__init__( *args, **kwargs )
        log.debug2("Form init: %s -> %s, %s", self.fields, args, kwargs)
        editing = bool( kwargs.get('instance') )
        obj = self.instance

        # Data fields that enrich class-level definitions
        self.autolookup_select_data = []

        # HACK - These will be overridden on save, avoid required field complaints
        # with root staff when they want to accept defaults
        if not editing and self.sandbox and self.user and self.user.is_root:
            if 'sandbox' in self.fields:
                self.fields['sandbox'].required = False
            if '_provider' in self.fields:
                self.fields['_provider'].required = False

        # HACK - Identify system-only items for provider_optional classes
        system_only = False
        if self.user and not self.user.access_root:
            if hasattr( obj, 'provider_optional' ) and obj.is_system:
                system_only = editing

        """
        Initialize values for any yaml fields
        The raw yaml field name is separated from getter, to support getter
        override (such as looking at an upstream default).
        If a value is only present in the combined yaml and not in the raw yaml,
        the value is from upstream. Only set these initial values if designated
        as an >> upstram field (otherwise they are left blank).
        """
        for name, config in self.yaml_form_fields.items():
            my_yaml = self.initial.get( name )
            if my_yaml:
                upstream_yaml = getattr( obj,
                            config.get( 'upstream_getter', '' ), None )
                # Convert the expandable names into yaml values and lookup
                for field_name in config['form_fields']:
                    upstream = field_name.startswith('>>')
                    field_name = field_name.strip('>>')
                    field = self.fields.get( field_name )
                    if field:
                        yaml_name = field_name.replace( '__', '.' )
                        value = my_yaml.get( yaml_name, None )
                        # Override with upstream if no downstream yaml value
                        if value is None and upstream and upstream_yaml:
                            value = upstream_yaml.get( yaml_name )
                        # Set the initial form value
                        if value:
                            self.initial[ field_name ] = value

        # Field and widget fixups
        my_widgets = getattr( self.Meta, 'widgets', {} )
        for name, field in self.fields.items():

            if '{' in field.help_text:
                field.help_text = replace_text_tags( field.help_text )

            # Swap in special MPF select widgets
            if( isinstance( field.widget, widgets.RelatedFieldWidgetWrapper ) ):
                model = obj._meta.get_field( name ).related_model

                # Use MPF multiple select
                if( isinstance( field.widget.widget, widgets.FilteredSelectMultiple ) ):
                    attrs = {}
                    if name in self.autolookup_fields:
                        attrs['data-app'] = model._meta.app_label
                        attrs['data-model'] = model._meta.model_name
                    field.widget.widget = mpSelectMultiple(
                                field.widget.widget.verbose_name.lower(),
                                is_stacked=False, choices=field.choices,
                                attrs=attrs )

                # Select2 autolookup
                elif( isinstance( field.widget.widget, forms.Select ) ):
                    if name in self.autolookup_fields:
                        field.widget.widget = mpSelect2()

                        # Populate initial value
                        init_value = {}
                        current = getattr( obj, name, None )
                        if current and current.wraps.id:
                            init_value = {
                                'id': current.wraps.id,
                                'name': str( current.wraps ),
                                }

                        self.autolookup_select_data.append({
                            'name': name,
                            'app': model._meta.app_label,
                            'model': model._meta.model_name,
                            'init_value': init_value,
                            })

            # Convert all DateTime widgets to use native date and time controls
            if( isinstance( field.widget, widgets.AdminSplitDateTime ) ):
                field.widget.widgets[0].input_type = 'date'
                field.widget.widgets[1].input_type = 'time'

            # Fixups for explicitly defined widgets
            widget = my_widgets.get( name )
            if widget:

                # Make any provider_optional CodeMirror widgets read-only for
                # non-root users to allow easy viewing and cut/paste
                # Also ensure root user always can edit
                if isinstance( widget, CodeEditor ):
                    if system_only:
                        field.widget.readonly = True

                # If a Checkbox multiple select has been specified in widgets,
                # to horizontal filtered select box when list gets too long
                # NOTE - bool check on a choices value that is a ModelChoiceIterator
                # does a len operation with FULL QUERYSET LOAD
                # DO NOT USE with fields without tenancy or with many rows
                choices = getattr( field, 'choices', [] )
                if( isinstance( widget, forms.CheckboxSelectMultiple ) and
                            len( choices ) > _MULT_CHOICE_THRESHOLD ):
                    model_field = obj._meta.get_field( name )
                    verbose_name = getattr( model_field, 'verbose_name', name )
                    field.widget.widget = mpSelectMultiple( verbose_name,
                                is_stacked=False, choices=field.choices )

            # Label fixups for Sitebuilder dynamic labels
            if( self.user and self.user.access_high and
                    hasattr( self.Meta, 'labels' ) and
                    hasattr( self.Meta, 'labels_sb' ) ):
                label = self.Meta.labels.get( name )
                sb_suffix = self.Meta.labels_sb.get( name )
                if label and sb_suffix:
                    field.label = mark_safe(
                        "{}<span class='mp_sb_label'>sb('{}')</span>".format(
                            label, sb_suffix ) )

    def clean( self ):
        """
        Manage saving of any designated yaml field that is assumed to only
        store non-default values or overriding an upstream value.
        Write any values into the yaml field ONLY if:
          - It already exists in local yaml
          - OR is different from upstream yaml
          - OR is Truthy if no upstream
        yaml fields are always in cleaned_data since they are added to form,
        so make sure they are available in POST.
        """
        for name, config in self.yaml_form_fields.items():
            if name in self.cleaned_data:
                my_yaml = getattr( self.instance, name )
                upstream_yaml = getattr( self.instance,
                            config.get( 'upstream_getter', '' ), None )
                for field_name in config['form_fields']:
                    field_name = field_name.strip('>>')
                    value = self.cleaned_data.get( field_name )
                    yaml_name = field_name.replace( '__', '.' )
                    # Always save if key already exists
                    write = yaml_name in my_yaml
                    # Otherwise only if different from upstream or Truthy
                    if not write:
                        if upstream_yaml and yaml_name in upstream_yaml:
                            write = value != upstream_yaml[ yaml_name ]
                        else:
                            write = bool( value )
                    # Write or clear the value from yaml field in form
                    if write:
                        if not value and yaml_name in my_yaml:
                            self.cleaned_data[ name ].pop( yaml_name )
                        else:
                            self.cleaned_data[ name ][ yaml_name ] = value
                    else:
                        self.cleaned_data[ name ].pop( yaml_name )
        return super().clean()
