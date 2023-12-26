#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Content admin shared across all content items
"""
from django import forms
from django.db import models

from mpframework.common import constants as mc
from mpframework.common.admin import mpListFilter
from mpframework.common.utils.strings import truncate
from mpframework.foundation.tenant.models.sandbox import Sandbox

from ..models import BaseContentVisibility
from .base_fields import BaseFieldForm
from .base_fields import BaseFieldAdmin


class BaseVisibilityForm( BaseFieldForm ):
    class Meta:
        model = BaseContentVisibility
        exclude = ()

        labels = dict( BaseFieldForm.Meta.labels, **{
            'sandboxes': "Available sites",
            'workflow': "Workflow visibility",
            })
        labels_sb = dict( BaseFieldForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseFieldForm.Meta.help_texts, **{
            'workflow': "'Production' content is visible to all users.",
            'sandboxes': "Select the sites this content is available in.",
            })
        widgets = dict( BaseFieldForm.Meta.widgets, **{
            'sandboxes': forms.CheckboxSelectMultiple(),
            })

    # User portal visibility
    # This is only enforced in client code, so content caching can ignore.
    # Although this can overlap with workflow and license visibility flag, it is
    # intended for seperation of types of content that is persistent, so not
    # related to editorial workflow or whether user has license.
    # Protected content access IS blocked based on this setting.
    portal__user_level = forms.ChoiceField( required=False, choices=(
            ('',  u"Public"),               # Everyone can see, including visitors
            ('A', u"Active users"),         # Any active user can see
            ('E', u"Extra content users"),  # Users with extra content on can see
            ('G', u"Group admins"),         # Group admins can see
            ('S', u"Staff"),                # Any staff level
            ),
            label="User visibility",
            help_text="Select the users that can see and access this content."
            )

    yaml_form_fields = {
        'sb_options':
            { 'form_fields': [
                'portal__user_level',
                ] }
        }


class RetiredFilter( mpListFilter ):
    title = "Retired"
    parameter_name = 'retired'
    def lookups( self, request, model_admin ):
        return [ ( 'hide', "Hide retired content" ),
                 ( 'only', "Only retired content" ),
                 ]
    def queryset( self, request, qs ):
        if self.value() == 'hide':
            return qs.exclude( workflow__in='QR' )
        if self.value() == 'only':
            return qs.filter( workflow__in='QR' )

class SandboxFilter( mpListFilter ):
    title = "Sites"
    parameter_name = 'sandbox'
    def lookups( self, request, _admin ):
        sandboxes = request.sandbox.provider.my_sandboxes.all()
        return [ (sb.pk, str(sb)) for sb in sandboxes ]
    def queryset( self, request, qs ):
        if self.value():
            return qs.filter( sandboxes__id=self.value() )


class BaseVisibilityAdmin( BaseFieldAdmin ):
    """
    Shared content functionality for sandbox and workflow visibility
    """
    form = BaseVisibilityForm

    list_text_small = BaseFieldAdmin.list_text_small + (
            'workflow', 'active_sandboxes' )
    list_col_med = BaseFieldAdmin.list_col_med + (
            'workflow', 'active_sandboxes' )
    list_hide_med = BaseFieldAdmin.list_hide_med + (
            'workflow', 'active_sandboxes' )

    list_filter_options = {
        'RetiredFilter': { 'default': 'hide' },
        }

    filter_mtm = dict( BaseFieldAdmin.filter_mtm, **{
            'sandboxes': ( Sandbox.objects, 'PROVIDER' ),
             })

    def save_related( self, request, form, formsets, change ):
        """
        Ensure current sandbox is set for use with new content
        Takes care of both staff who don't see sandboxes and easy mistake of
        creating a new content item without checking any sandboxes.
        """
        super().save_related( request, form, formsets, change )
        if not change and not request.user.logged_into_root:
            form.instance.sandboxes.add( request.sandbox )

    def get_queryset( self, request ):
        """
        Add items to queryset that must be derived at request time
        """
        qs = super().get_queryset( request )

        # Create unique sum for each set of sandboxes for sorting
        qs = qs.annotate(
                _sandboxes_sum = models.Sum( 'sandboxes__id', distinct=True ),
                )
        return qs

    def get_fieldsets( self, request, obj=None ):
        """
        Adjust fields based on user privilege
        """
        rv = super().get_fieldsets( request, obj )

        # Add sandboxes and workflow to top block
        update = ( 'workflow' ,)
        if request.user.sees_sandboxes or request.user.access_root:
            update += ( 'sandboxes' ,)
        rv[ self.fs_top ][1]['fields'].append( update )

        return rv

    def get_list_display( self, request ):
        """
        Add Sandbox to changelist is user can see
        """
        rv = list( super().get_list_display( request ) )
        user = request.user

        if not user.sees_sandboxes and 'active_sandboxes' in rv:
            rv.remove('active_sandboxes')

        return rv

    def get_list_filter( self, request ):
        """
        Add filters user can see
        """
        rv = list( super().get_list_filter( request ) )
        user = request.user

        if user.sees_sandboxes:
            rv = [ SandboxFilter ] + rv
        if user.access_med:
            rv = [ RetiredFilter, 'workflow' ] + rv

        return rv

    def active_sandboxes( self, obj ):
        # FUTURE - obj not using prefetched sandboxes here, try to get rid of extra value_list call
        return truncate( u", ".join([ subdomain for subdomain in
                                     obj.sandboxes.values_list( 'subdomain', flat=True ) ]),
                         mc.CHAR_LEN_UI_DEFAULT )
    active_sandboxes.short_description = u"Active sites"
    active_sandboxes.admin_order_field = '_sandboxes_sum'
