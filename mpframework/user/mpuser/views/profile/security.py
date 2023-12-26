#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Form view for username/password update
"""
from django import forms
from django.urls import reverse_lazy
from django.http import HttpResponseRedirect
from django.contrib.auth import update_session_auth_hash
from django.template.response import TemplateResponse
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache

from mpframework.common import log
from mpframework.common.view import ssl_required
from mpframework.common.view import login_required
from mpframework.common.form import BaseModelForm

from ...models import mpUser
from ...forms.create import mpUsernameBaseFormMixin
from ...forms.password import ChangePasswordForm


class mpUsernameForm( mpUsernameBaseFormMixin, BaseModelForm ):
    class Meta:
        model = mpUser
        fields = ( 'email' ,)

        widgets = dict( BaseModelForm.Meta.widgets, **{
                'email': forms.TextInput(attrs={'size': 40 }),
                })

    def __init__( self, sandbox, *args, **kwargs ):
        super().__init__( *args, **kwargs )
        # Stash sandbox for user validation
        self.set_sandbox( sandbox )

    def clean_email( self ):
        """
        Make sure the email is not in use
        """
        email = self.cleaned_data.get('email')
        self.validate_email( email )
        return email

    def save( self, commit=True ):
        """
        Special save is necessary to change username
        """
        if commit:
            self.instance.update_username( self.cleaned_data.get('email') )


@sensitive_post_parameters()
@ssl_required
@login_required
@never_cache
def update_security( request ):
    """
    Update username and password
    """
    user = request.user
    sandbox = request.sandbox

    username_form = mpUsernameForm( sandbox )
    password_form = ChangePasswordForm( user )

    if request.method == "POST":

        if 'update_username' in request.POST:
            username_form = mpUsernameForm( sandbox, request.POST, instance=user )
            if username_form.is_valid():
                log.info2("USERNAME CHANGE: %s ->%s", request.mpipname,
                            username_form.cleaned_data.get('email') )
                username_form.save()

        if 'update_password' in request.POST:
            password_form = ChangePasswordForm( user, request.POST )
            if password_form.is_valid():
                log.info2("PASSWORD CHANGE: %s", request.mpipname)
                password_form.save()

                # Logout any users logged in
                update_session_auth_hash( request, password_form.user )
                return HttpResponseRedirect( reverse_lazy('pwd_change_done') )

    return TemplateResponse(request, 'user/profile/security.html', {
                'username_form': username_form,
                'password_form': password_form,
                })
