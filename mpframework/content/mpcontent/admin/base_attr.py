#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Admin shared between everything by portal_group
"""
from mpframework.common import log

from ..models import BaseAttr
from .base_visibility import BaseVisibilityForm
from .base_visibility import BaseVisibilityAdmin


class BaseAttrForm( BaseVisibilityForm ):
    class Meta:
        model = BaseAttr
        exclude = ()

        labels = dict( BaseVisibilityForm.Meta.labels, **{
            })
        labels_sb = dict( BaseVisibilityForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseVisibilityForm.Meta.help_texts, **{
            })
        widgets = dict( BaseVisibilityForm.Meta.widgets, **{
            })

    yaml_form_fields = BaseVisibilityForm.yaml_form_fields.copy()


class BaseAttrAdmin( BaseVisibilityAdmin ):
    """
    Shared behavior for admin of BaseAttr types
    Most functionality defined here is shared between Attrs and Items,
    while some is used by Attrs admin directly, and other parts are
    overridden in the BaseItem admin. Goals is to minimize overall code.
    """
    form = BaseAttrForm

    def get_queryset( self, request ):
        """
        Add items to queryset that must be derived at request time
        """
        qs = super().get_queryset( request )

        # Limit to specific sandboxes if requested
        # Used for popup field lookup screen
        if request.is_popup:
            qs = qs.filter( sandbox=request.sandbox )

        return qs

    def get_fieldsets( self, request, obj=None ):
        """
        Adjust fields based on user privilege
        """
        rv = super().get_fieldsets( request, obj )

        # Assume root is the last fieldset
        if request.user.access_root_menu:
            rv[ -1 ][1]['fields'].append((
                '_provider',
                ))

        return rv

    def change_view( self, request, object_id, form_url='', extra_context=None ):
        response = super().change_view( request,
                    object_id, form_url, extra_context )
        # Support pop-up editing screens returning
        if request.GET.get('return_to'):
            redirect = str( request.GET.get('return_to') )
            log.debug("Redirecting to: %s", redirect)
            response['location'] = redirect

        return response

    def get_changelist_form( self, request, **kwargs ):
        """
        Use normal form widgets for any inline editing
        """
        return self.form
