#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User Profile editing forms
"""

from django import forms

from mpframework.common import constants as mc

from . import BaseModelForm


class EmailInviteForm( BaseModelForm ):

    class Meta:

        fields = ( 'emails' ,)

        widgets = {
                'emails': forms.Textarea( attrs={'rows':12, 'cols':mc.CHAR_LEN_UI_EMAIL} ),
                }
