#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    User app's user profile management
"""
from django import forms
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common import constants as mc
from mpframework.common.form import BaseModelForm
from mpframework.common.form import respond_ajax_model_form
from mpframework.common.view import login_required

from ...models import mpUser


class mpUserProfileForm( BaseModelForm ):
    class Meta:
        model = mpUser

        fields = (
                'first_name', 'last_name', 'image',
                'organization', 'title', 'comments',
                'external_tag', 'external_tag2', 'external_tag3',
                )

        widgets = dict( BaseModelForm.Meta.widgets, **{
            'first_name': forms.TextInput( attrs={'size': 32 } ),
            'last_name': forms.TextInput( attrs={'size': 32 } ),
            'organization': forms.TextInput( attrs={'size': 48 } ),
            'title': forms.TextInput( attrs={'size': 48 } ),
            'external_tag': forms.TextInput( attrs={'size': 48 } ),
            'external_tag2': forms.TextInput( attrs={'size': 48 } ),
            'external_tag3': forms.TextInput( attrs={'size': 48 } ),
            'comments': forms.Textarea( attrs=mc.UI_TEXTAREA_LARGE ),
            })

@login_required
def manage_info( request ):
    """
    User-editable values for their profile
    """
    user = request.user

    if request.method == "POST":
        form = mpUserProfileForm( request.POST, instance=user, files=request.FILES )
        if form.is_valid():
            log.info2("Updating user profile: %s -> %s", request.mpipname, request.POST)
            form.save()

        if request.is_api:
            return respond_ajax_model_form( request, user )

    else:
        form = mpUserProfileForm( instance=user )

    return TemplateResponse( request, 'user/profile/manage.html', {
                'form': form,
                })
