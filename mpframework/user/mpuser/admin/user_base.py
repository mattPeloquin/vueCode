#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared functionality for user management

    FUTURE - Move account support into mpExtend
"""
from django import forms
from django.db.models import Q
from django.contrib.auth.forms import ReadOnlyPasswordHashField

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.delivery import DELIVERY_MODES_ALL, DELIVERY_MODES_STAFF
from mpframework.common.form import BaseModelForm
from mpframework.common.admin import mpListFilter
from mpframework.common.widgets import CodeEditor
from mpframework.foundation.tenant.admin import BaseTenantAdmin

from ..models import mpUser
from .user_django import DjangoPasswordAdminMixin


class mpUserChangeForm( BaseModelForm ):
    """
    This form is used for editing user values in provider and root admin
    """
    class Meta:
        model = mpUser
        exclude = ()

        labels = dict( BaseModelForm.Meta.labels, **{
            'is_active': "Can log in",
            'sandboxes_level': "Multi-site visibility",
            '_staff_level': "Staff level",
            'staff_areas': "Staff areas",
            'is_superuser': "Vueocity account manager",
            '_is_owner': "Vueocity account owner",
            'workflow_level': "Workflow level",
            'staff_user_view': "Currently in user test view",
            'external_tag': "User report tags",
            'external_tag2': "",
            'external_tag3': "",
            'external_key': "Staff external ID",
            'external_group': "Staff custom group",
            'organization': "Company, group, team, etc.",
            'title': "Title or responsibility",
            'init_terms': "Terms accepted",
            'init_activation': "Account activation details",
            '_delivery_mode': "Content protection level",
            '_extended_access': "User has access to extended content",
            })
        help_texts = dict( BaseModelForm.Meta.help_texts, **{
            'email': "Username for login, and primary contact email",
            'is_active': "Disable to temporally prevent the user from logging in",
            'sandboxes_level': "Can this staff member log into, see, and change all sites "
                    "associate with this account?",
            '_staff_level': "Make user a staff member and set the level of "
                    "customization and features they can see.",
            'is_superuser': "Managers can add new staff and modify staff settings",
            '_is_owner': "Owners can access Vueocity account billing and features.",
            'workflow_level': "The current workflow visibility for this user",
            'staff_areas': "Feature areas this staff member has access to: "
                    "C=Content, U=User, P=Product catalog, S=Sandbox, G=Group accounts (blank for all)",
            'staff_user_view': "Checked when staff member has selected "
                    "user test view, which hides their staff UI and content access.",
            'organization': "User-controlled name for their company, organization, group, team, etc. "
                    "This is included in group admin reports.",
            'title': "User-controlled field for job title, included in group admin reports.",
            'external_tag3': "Fields to add ID, code, etc. for searching and reporting.",
            'external_key': "ID, code, key, etc. to tie account to external system such as "
                    "Salesforce (users do not see).",
            'external_group': "Define names/codes to group accounts for reporting and/or "
                    "connecting to external systems (users do not see)",
            'image': "Optional avatar image the user can upload.",
            '_delivery_mode': "Override content protection level to resolve problems "
                    "accessing content in some user networks.",
            '_extended_access': "Content may be optionally marked as visible only "
                    "to users with extended visibility.",
            })
        widgets = dict( BaseModelForm.Meta.widgets, **{
            'first_name': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'last_name': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'organization': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'title': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'init_terms': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'init_activation': forms.TextInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'email': forms.EmailInput( attrs=mc.UI_TEXT_SIZE_DEFAULT ),
            'comments': forms.Textarea( attrs=mc.UI_TEXTAREA_DEFAULT ),
            'options': CodeEditor( mode='yaml', theme='default', rows=12 ),
            })

    # Don't show password; use Django pwd field to provide form interaction, and place
    # the link to change password in button.
    # Suppress Django's display of hash info, by changing the widget
    password = ReadOnlyPasswordHashField(
            label = "",
            help_text = "<a href='../password/' class='mp_button'> Change user's password </a>",
            widget = forms.HiddenInput()
            )

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        # Allow override with more specialized modes
        if self.fields.get('_delivery_mode'):
            if self.user and self.user.access_root:
                self.fields['_delivery_mode'].choices = DELIVERY_MODES_ALL
            else:
                self.fields['_delivery_mode'].choices = DELIVERY_MODES_STAFF

    def clean( self ):
        """
        Make sure requested actions won't place sandbox or user into invalid state
        """
        rv = super().clean()
        log.debug("User change form errors: %s", self._errors)

        # The user making the change; different from user being modified
        provider = self.sandbox.provider
        if self.user and not self.user.access_root:

            # Last superuser and owner for provider can't remove their status
            if self.cleaned_data.get('id') == self.user.id:
                qs = mpUser.objects.filter( _provider=provider ).exclude( id=self.user.pk )
                if self.user.is_superuser:
                    if qs.filter( is_superuser=True ).count() < 1:
                        log.info("Last superuser tried to give up superuser: %s", self.user)
                        raise forms.ValidationError(
                                u"One account manager is required; "
                                "please select account manager as you are the last one")
                if self.user.is_owner:
                    if qs.filter( _is_owner=True ).count() < 1:
                        log.info("Last owner tried to give up owner: %s", self.user)
                        raise forms.ValidationError(
                                u"One owner is required; "
                                "please select owner as you are the last one")

            # Can only promote user to all sandboxes if they don't have conflicting accounts
            if self.cleaned_data.get('sandboxes_level') > 0:
                email = self.cleaned_data.get('email')
                if mpUser.objects.filter( _provider=provider, email=email ).count() > 1:
                    raise forms.ValidationError(
                            u"User registered with multiple sites: "
                            "{}\nChange the other emails to see all sites.".format( email ) )
        return rv


class ReadyFilter( mpListFilter ):
    """
    Custom filter to identify orphan accounts
    """
    title = "User account activation"
    parameter_name = 'ready'
    _orphan_query = Q(init_activation='') | Q(init_terms='')
    def lookups( self, request, model_admin ):
        return (
            ('READY', 'Activated users'),
            ('ORPHANS', 'Activation/Terms pending'),
            )
    def queryset( self, request, qs ):
        if self.value() == 'READY':
            return qs.exclude( self._orphan_query )
        if self.value() == 'ORPHANS':
            return qs.filter( self._orphan_query )


class mpUserAdminBase( DjangoPasswordAdminMixin, BaseTenantAdmin ):
    """
    Base management screens for users, replaces Django user admin
    """
    form = mpUserChangeForm
    can_add_item = False

    list_display_links = ( 'email' ,)
    ordering = ( '-last_login' ,)

    search_fields = ( 'email', 'first_name', 'last_name',
            'external_key', 'external_group', 'organization', 'title',
            'external_tag', 'external_tag2', 'external_tag3' )

    readonly_fields = BaseTenantAdmin.readonly_fields + ( '_primary_account' ,)

    def get_queryset( self, request ):
        """
        Optimize the DB access of account users
        """
        qs = super().get_queryset( request )
        qs = qs.select_related( 'account_user', 'account_user__primary_account' )
        return qs

    fieldsets = [
        ('', {
            'classes': ('mp_collapse',),
            'fields': [
                ('first_name','last_name'),
                ('email','password'),
                ('is_active',),            # Workflow level added based on privilege
                ('_delivery_mode','_primary_account'),
                ]
            }),
        ("Staff access", {                 # Only superusers see this
            'classes': ('mp_collapse',),
            'fields': [
                ('_staff_level','staff_user_view'),
                ('is_superuser',),         # Owner added based on privilege
                ]
            }),
        ("User information", {
            'classes': ('mp_collapse mp_closed',),
            'fields': [
                'image',
                ('organization','title'),
                ('external_group','external_key'),
                'external_tag',
                'external_tag2',
                'external_tag3',
                'comments',
                ]
            }),
        ("History", {
            'mp_staff_level': 'access_med',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                ('hist_created','email_verified'),
                'hist_modified',
                'init_terms',
                'init_activation',
                )
            }),
        ('ROOT', {
            'mp_staff_level': 'access_root_menu',
            'classes': ('mp_collapse mp_closed',),
            'fields': (
                ('_sandbox','_provider'),
                '_has_test_access',
                ('email_changed','pwd_changed'),
                'options',
                )
            }),
        ]

    def get_fieldsets( self, request, obj=None ):
        user = request.user
        rv = super().get_fieldsets( request, obj )

        if user.access_low:
            rv[0][1]['fields'][2] += ( 'workflow_level' ,)

        if user.access_med:
            rv[0][1]['fields'].append( ('_extended_access',) )
            rv[1][1]['fields'].append( ('staff_areas','sandboxes_level') )

        if user.is_owner:
            rv[1][1]['fields'][1] += ( '_is_owner' ,)

        return rv

    def _staff( self, obj ):
        return obj.is_staff
    _staff.short_description = "Staff"
    _staff.admin_order_field = '_staff_level'
    _staff.boolean = True

    def _superuser( self, obj ):
        return obj.is_superuser
    _superuser.short_description = "Manager"
    _superuser.admin_order_field = 'is_superuser'
    _superuser.boolean = True

    def _owner( self, obj ):
        return obj._is_owner
    _owner.short_description = "Owner"
    _owner.admin_order_field = '_is_owner'
    _owner.boolean = True

    def _ready( self, obj ):
        return obj.is_ready()
    _ready.short_description = "Ready"
    _ready.boolean = True

    def _primary_account( self, obj ):
        if not obj.au:
            return ""
        account = obj.au.primary_account
        if not account:
            return ""
        if account.is_group:
            return account.name
        return u"Individual"
    _primary_account.short_description = "Primary account"

    def _all_sandboxes( self, obj ):
        return obj.sees_sandboxes
    _all_sandboxes.short_description = "Sees all sites"
    _all_sandboxes.admin_order_field = 'sandboxes_level'
    _all_sandboxes.boolean = True

    def formfield_for_choice_field( self, db_field, request, **kwargs ):

        # Remove access level choices user can't see
        if db_field.name == '_staff_level':
            user = request.user
            choices = ()
            max_level = user.sandbox.policy['staff_level_max']
            if user.access_staff and user.is_superuser and max_level:
                staff_levels = ()
                for level, name in mpUser.STAFF_LEVELS:
                    if level is None or level <= max_level:
                        staff_levels += (( level, name ),)
                choices += staff_levels
                if user.access_root:
                    choices += mpUser.ROOT_LEVELS
            kwargs['choices'] = choices

        return super().formfield_for_choice_field( db_field, request, **kwargs )

    def has_add_permission( self, request ):
        # Enforce policy limits
        can_add = super().has_add_permission( request )
        if can_add:
            can_add = self.model.objects.limits_ok(
                        _provider=request.sandbox.provider )
        return can_add

    def save_model( self, request, obj, form, change ):
        """
        Add security checks on user save to prevent an escalation of privilege
        by unauthorized user (such as with a fake POST).

        Scenarios guarded here aren't possible in UI as they shouldn't be visible
        AND Django admin's form doesn't accept POST parameters that aren't part of
        the admin fieldset for a request.
        This hardening is for POST attacks outside the UI, and programming/config
        errors that could show part of the UI when it shouldn't.
        """
        user = request.user
        sandbox = request.sandbox

        # Don't run security checks on a root user
        if not user.access_root:

            # Make sure user making change is from same provider
            if not ( obj._provider == sandbox.provider == user._provider ):
                raise Exception("SUSPECT ATTACK - Non-root modify provider:"
                        " %s -> %s" % (request.mpipname, obj))

            # There's no scenario for changing a provider
            if '_provider' in form.cleaned_data:
                raise Exception("SUSPECT ATTACK - Non-root change provider:"
                        " %s -> %s" % (request.mpipname, obj))

            # Only root can set root
            if obj.staff_level > mc.STAFF_LEVEL_ALL:
                log.warning("SUSPECT ATTACK - set ROOT staff level: %s -> %s",
                            request.mpipname, obj)
                obj._staff_level = user.staff_level

            if not user.is_superuser:

                # Only superusers promote superusers (first superuser is bootstrapped)
                if obj.is_superuser:
                    log.warning("SUSPECT ATTACK - set superuser: %s -> %s",
                                request.mpipname, obj)
                    obj.is_superuser = False

                # Only superusers can promote higher privilege on themselves
                if user.staff_level < obj.staff_level:
                    log.warning("SUSPECT ATTACK - escalate staff level: %s -> %s",
                                request.mpipname, obj)
                    obj._staff_level = user.staff_level

                # Only superusers with sees sandbox can promote to sees sandboxes
                if user.sandboxes_level < obj.sandboxes_level:
                    log.warning("SUSPECT ATTACK - escalate sandboxes level: %s -> %s",
                                request.mpipname, obj)
                    obj.sandboxes_level = user.sandboxes_level

            # Only owners can promote owners
            if not user.is_owner and obj.is_owner:
                log.warning("SUSPECT ATTACK - set owner: %s -> %s", request.mpipname, obj)
                obj.is_owner = False

            # When downgrading user from sees sandboxes, need to make sure sandbox is set
            if obj.sandboxes_level <= 0:
                obj._sandbox = sandbox
            else:
                obj._sandbox = None

        super().save_model( request, obj, form, change )
