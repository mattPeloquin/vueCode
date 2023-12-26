#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Base Admin for MPF model classes
"""
from copy import deepcopy
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from django.contrib.admin.helpers import flatten_fieldsets
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from .. import log
from ..form import respond_ajax_model_form
from ..model.utils import field_names
from ..utils.http import append_querystring
from .base_admin import BaseAdmin


class BaseModelAdmin( BaseAdmin ):
    """
    Base Admin for models derived from MPF BaseModel
    """
    _ROOT_ADMIN_ONLY_FIELDS = ( '_provider' ,)
    list_add_root = ('id', 'hist_modified', 'hist_created')

    # Responsive support, assuming size breakpoints and css names
    list_hide_med = ('hist_created',)
    list_hide_small = ('hist_modified', 'id', 'notes')
    list_text_small = ('description', 'notes')
    list_text_xsmall = ('hist_created', 'hist_modified')
    list_col_small = ('id',)
    list_col_med = ('hist_created', 'hist_modified')
    list_col_large = ('name',)
    list_col_xlarge = ('description', 'notes')

    # Control whether user can add new item on changelist or in dialog
    can_add_item = True
    can_add_item_everywhere = False

    # Allow configuring field sets to only be visible with certain permissions
    super_only_fieldsets = ()

    # Designate ready-only fields at different levels of access
    # Unlike field hiding, readonly fields must refer to a field in this admin instance,
    # so can only name fields that will be present in all instances in a hierarchy
    readonly_fields = ( 'hist_created', 'hist_modified' )
    super_edit_fields = ()
    root_edit_fields = ()

    # Immutable fields can be set on creation/copy, but normally never again
    immutable_fields = ()

    # By default, root user logged into root site has same privledges
    # because some dynamic fields must be treated as readonly in root due to
    # long lists slowing down the UI - use this to specifically override
    # on a case by case basis
    rootsite_readonly_fields = ()

    # Assume staff notes are shown
    hide_notes = False

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        # Stash model field names for use in introspection
        self.field_names = field_names( self.model )

    def has_add_permission( self, request ):
        """
        Setup default add permission for MPF specific behavior:
         - Honor user staff level
         - Hide Django's '+' buttons by default to increase usability
        """
        # First check MPF admin and user privilege settings
        can_add = self.can_add_item and request.user.access_low

        # Then unless add everywhere is allowed, only allow add on admin
        # screens for this specific model
        if can_add and not self.can_add_item_everywhere:
            try:
                model = self.model.__name__.lower()
                can_add = '/{}'.format( model ) in request.mppath
            except Exception:
                pass

        return can_add

    def save_model( self, request, obj, form, change ):
        """
        Guard against critical POST attacks that could circumvent UI
        """
        assert form.cleaned_data
        user = request.user
        if not user.access_root:
            sandbox = request.sandbox

            # There's no scenario for changing a provider
            if any( k in form.cleaned_data for k in ('_provider', 'provider_optional') ):
                raise Exception("SUSPECT ATTACK - Change provider via admin:"
                        " %s -> %s => %s" % (sandbox, user, obj))

            # Prevent modifying provider optional items
            if hasattr( obj, 'provider_optional' ) and obj.is_system:
                raise Exception("SUSPECT ATTACK - Modify system item:"
                        " %s -> %s => %s" % (sandbox, user, obj))

        super().save_model( request, obj, form, change )

    # Add copy/delete if available
    def list_actions( self, obj ):
        action_html = ''
        if self.can_copy:
            action_html += format_html(
                    '<a class="mp_admin_copy mp_button_flat" href="{}">Copy</a>',
                    self.change_url( obj, copy=True ) )
        if self.can_delete:
            action_html += format_html(
                    '<a class="mp_admin_delete mp_button_flat" href="{}">Delete</a>',
                    self.delete_url( obj ) )
        return mark_safe( action_html )
    list_actions.short_description = ""
    def change_url( self, obj, copy=False ):
        rv = reverse( 'admin:%s_%s_change' % ( obj._meta.app_label,
                                               obj._meta.model_name ),
                       args=( obj.pk ,),
                       current_app=self.admin_site.name )
        if copy:
            # FUTURE - replace admin copy save as with copy API based on cloning
            rv += '?mpf_admin_copy_request=1'
        return rv
    def delete_url( self, obj ):
        rv = reverse( 'admin:%s_%s_delete' % ( obj._meta.app_label,
                                               obj._meta.model_name ),
                       args=( obj.pk ,),
                       current_app=self.admin_site.name )
        return rv

    def get_changelist(self, request, **kwargs):
        """
        Make sure readonly users can't access editable lists
        """
        if request.user.access_ro:
            self.list_editable = ()
        return super().get_changelist( request,**kwargs )

    def get_fieldsets( self, request, obj=None ):
        """
        Field overrides common to all admin screens
        """
        rv = deepcopy( super().get_fieldsets( request, obj ) )

        # Ensure inlines can be modified by MPF options
        self.inlines = list( self.inlines )

        # Add after create fieldsets, assuming ROOT section is last
        if obj and self.after_create_fieldsets:
            rv[-1:-1] = deepcopy( self.after_create_fieldsets )

        self._remove_fieldsets( request.user, rv )

        if request.user.access_high:
            self._add_notes( request.sandbox, rv )

        return rv

    def _remove_fieldsets( self, user, fieldsets ):
        """
        Remove fieldset panes user can't see
        """
        def _fieldset_access( fs ):
            try:
                # First check if staff level is valid
                # mp_staff_level key must be removed or Django will revolt
                fieldset_level = fs[1].pop( 'mp_staff_level', '' )
                access = not fieldset_level or getattr( user, fieldset_level )
                log.detail3("Access check: %s -> %s -> %s >= %s",
                               user, fs[0], user.staff_level, fieldset_level )
                # Next see if any superuser fieldsets should be hidden
                if access and not user.is_superuser:
                    for name in self.super_only_fieldsets:
                        if fs[0].startswith( name ):
                            access = False
                            log.detail3("Removing %s from fieldset", name)
                            break
                # If removed fieldset's name matches an inline class, remove it
                # HACK - this relies on class name entered in fieldset matching inline
                if not access:
                    for inline in self.inlines:
                        if fs[0] == inline.__name__:
                            self.inlines.remove( inline )
                            break
                return access
            except Exception:
                log.exception("Problem setting admin access level")
        fieldsets[:] = [ fs for fs in fieldsets if _fieldset_access( fs ) ]

    def _add_notes( self, sandbox, fieldsets ):
        """
        HACK - add note field to admin based on access and settings
        """
        if ( self.all_fields and ( not self.hide_notes ) and
                ( not 'notes' in self.all_fields ) and
                'notes' in self.field_names ):
            # Option to make prominent in UI
            if sandbox.options['staff.notes_top']:
                fieldsets[0][1]['fields'] = ['notes'] + list( fieldsets[0][1]['fields'] )
            # Otherwise attach to history section if present
            else:
                for fieldset in fieldsets:
                    if fieldset[0] and "history" in fieldset[0].lower():
                        fieldset[1]['fields'] = ['notes'] + list( fieldset[1]['fields'] )
            # Reset all_fields caching for new notes
            self._all_fields = None

    @property
    def _field_names( self ):
        """
        Safe way to get all field names before self.fields is set
        """
        if self.fieldsets:
            return flatten_fieldsets( self.fieldsets )
        else:
            return list( set(
                [ field.name for field in self.opts.local_fields ] +
                [ field.name for field in self.opts.local_many_to_many ]
                ))

    def get_readonly_fields( self, request, obj=None ):
        """
        Adjust read-only fields based on privilege
        """
        user = request.user

        # If user has read-only permissions, they can't modify anything
        if user.access_ro:
            return self._field_names

        # Allow fewer constraints on root user logged into root
        if user.logged_into_root:
            return self.rootsite_readonly_fields

        rv = list( self.readonly_fields )

        # Make certain fields only modifiable by root
        if not user.access_root:
            for field in self._ROOT_ONLY_FIELDS:
                if field in self.field_names:
                    rv.append( field )

        # Then add read-only fields based on permission
        if not user.is_superuser:
            rv += self.super_edit_fields
        if not user.is_root:
            rv += self.root_edit_fields

        # HACK - immutable fields that have values that do not
        # end in copy are placed in ready only
        if obj:
            for field in self.immutable_fields:
                value = getattr( obj, field, None )
                if value and not str(value).endswith('copy'):
                    rv.append( field )
        return rv

    # MPF additions for returns from admin operations

    def response_redirect( self, request ):
        """
        Override Save response to return by default to the URL it came from
        vs. changelist. Also support URL in query string or admin config.
        """
        if any([ op in request.POST for op in
                ['_saveasnew', '_continue', '_addanother'] ]):
            return
        url = request.GET.get('admin_redirect')
        if not url:
                url = self.response_url( request )
        if url:
            log.debug("Returning after admin: %s -> %s", request.mpname, url)
            return HttpResponseRedirect( url )

    def response_url( self, request ):
        # Override for a configured redirect
        return

    def response_add( self, request, obj ):
        # Replace saveasnew with copy support
        if '_saveasnew' in request.POST:
            return self._handle_copy( request, obj )
        # Support returning to previous location
        redirect = self.response_redirect( request )
        if redirect:
            return redirect
        # Otherwise default Django
        return super().response_add( request, obj )

    def response_change( self, request, obj ):
        # Support ajax save for "Save and continue"
        if request.is_api:
            return respond_ajax_model_form( request, obj )
        # Support returning to previous location
        redirect = self.response_redirect( request )
        if redirect:
            return redirect
        # Otherwise default Django
        return super().response_change( request, obj )

    def _handle_copy( self, request, obj ):
        """
        Override Django's save as new to provide copy functionality
        """
        msg = format_html( '{} was copied successfully.', obj )
        self.message_user( request, msg, messages.SUCCESS )
        # Redirect to the new object
        redirect_url = self.change_url( obj )
        redirect_url = append_querystring( redirect_url, mpf_admin_copy_new=1 )
        return HttpResponseRedirect( redirect_url )
