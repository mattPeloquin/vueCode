#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    LMS related forms
"""
from django import forms

from mpframework.common.form import parsleyfy
from mpframework.common.form import mpFileFormField

from .models import Package


@parsleyfy
class PackageFormMixin:
    """
    Provides package fields for use on forms
    FUTURE - is there need for new package form fields to be created in constructor?
    """
    FIELD_NAMES = ['package_file', 'package_type', 'package_lms']

    def __init__( self, *args, **kwargs ):
        super().__init__( *args, **kwargs )

        self.fields['package_file'] = mpFileFormField( required=True,
                                                protected=True,
                                                label="Package zip file" )
        self.fields['package_type'] = forms.ChoiceField( choices=Package.PACKAGE_TYPE,
                                                label="Package type" )
        self.fields['package_lms'] = forms.ChoiceField( choices=Package.LMS_TYPE,
                                                label="LMS publishing" )

    def package_values( self ):
        return tuple( [ str( self.cleaned_data.get( field_name ) ) for
                        field_name in self.FIELD_NAMES ] )
