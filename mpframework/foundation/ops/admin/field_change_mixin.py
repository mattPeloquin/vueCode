#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Mixin for admin classes to track field changes
"""
from mpframework.common import log
from mpframework.common.utils.strings import close_compare

from ..models.field_change import FieldChange


class FieldChangeMixin:
    """
    Store changes to specific fields
    MUST BE INHERITED FIRST TO ENSURE OBJECT NOT UPDATED WITH FORM VALUE
    """
    changed_fields_to_save = ()

    def save_model( self, request, obj, form, change ):
        """
        Manage caching while saving; update version so dependencies are invalidated
        """
        if change:
            user = request.user
            sandbox = request.sandbox

            for field in self.changed_fields_to_save:
                try:
                    # Need to verify the value actually changed, including in cases
                    # where the object may have value, but was never in the form
                    new_value = form.cleaned_data.get( field, '' )
                    old_value = form.initial.get( field, '' )
                    if ( field in form.changed_data and
                            bool(new_value) ^ bool(old_value) ):
                        if close_compare( old_value, new_value ):
                            log.debug2("Processing save_model change for: %s -> %s - %s", user, self, field)

                            description = u"Updated {} for {}".format(
                                        obj._meta.get_field( field ).verbose_name,
                                        obj._meta.verbose_name )

                            new_change = FieldChange(
                                            sandbox=sandbox,
                                            user=user,
                                            content_object=obj,
                                            field=field,
                                            desc=description,
                                            value=old_value )
                            new_change.save()

                except Exception:
                    log.exception("Problem saving changed field: %s -> %s -> %s", sandbox, user, field)

        super().save_model( request, obj, form, change )
