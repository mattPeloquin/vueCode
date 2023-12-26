#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Views for extending admin functionality
"""
from django import forms

from mpframework.common import log
from mpframework.common.view import staff_required
from mpframework.common.form import BaseForm

from ...mpcontent.models import LmsItem
from ..forms import PackageFormMixin


class PackageUpdateForm( PackageFormMixin, BaseForm ):
    """
    Used to upload new packages for an lms item
    """

    # Set by Javascript based on the current lms item
    lms_id = forms.CharField( widget=forms.HiddenInput() )


@staff_required
def lms_update_subview( request, convert_post_to_get=True ):
    """
    Sub view for submits from the upload new package dialog
    """
    package_update_form = PackageUpdateForm( auto_id='update_%s' )

    if 'POST' == request.method:

        if 'upload_package' in request.POST:
            package_update_form = PackageUpdateForm( request.POST, request.FILES, auto_id='update_%s' )
            if package_update_form.is_valid():
                log.debug("Upload new package requested: %s", package_update_form.cleaned_data)
                lms = LmsItem.objects.get( id=package_update_form.cleaned_data.get('lms_id') )
                file_name, package_type, lms_type = package_update_form.package_values()
                file_data = request.FILES.get('package_file')

                lms.update_package( file_name, file_data, package_type,
                                    lms_type, request.user )

            else:
                log.info("Form validation for new package failed: %s", package_update_form.errors)

            request.method = 'GET' if convert_post_to_get else request.method

    return package_update_form

