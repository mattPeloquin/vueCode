#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Views for extending admin functionality
"""

from mpframework.common import log
from mpframework.common.view import staff_required
from mpframework.common.events import sandbox_event
from mpframework.content.mpcontent.admin import BaseItemForm

from ...mpcontent.models import LmsItem
from ..forms import PackageFormMixin


class NewLmsItemForm( PackageFormMixin, BaseItemForm ):
    class Meta:
        model = LmsItem
        fields = [ '_name', 'tag', 'workflow' ]


@staff_required
def lms_add_subview( request, convert_post_to_get=True ):
    """
    Sub view for submits from the lms item add package dialog
    """
    new_lms_form = NewLmsItemForm( auto_id='lms_%s' )

    if 'POST' == request.method:

        if 'add_lms' in request.POST:
            new_lms_form = NewLmsItemForm( request.POST, request.FILES, auto_id='lms_%s' )
            if new_lms_form.is_valid():
                log.debug("Add LMS package requested: %s", new_lms_form.cleaned_data)
                file_data = request.FILES.get('package_file')
                file_name, package_type, lms_type = new_lms_form.package_values()
                name = new_lms_form.cleaned_data.get('_name')

                LmsItem.objects.create_obj( sandbox=request.sandbox,
                        _name=name,
                        tag=new_lms_form.cleaned_data.get('tag'),
                        workflow=new_lms_form.cleaned_data.get('workflow'),
                        file_name=file_name, file_data=file_data,
                        package_type=package_type, lms_type=lms_type
                        )

                sandbox_event( request.user, 'content_lms_new', name, file_name )
            else:
                log.info("Form validation for new lms item failed: %s", new_lms_form.errors)

            request.method = 'GET' if convert_post_to_get else request.method

    return new_lms_form


