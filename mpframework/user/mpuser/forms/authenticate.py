#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Django forms used with user
"""
from django import forms
from django.contrib.auth import authenticate
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.signals import user_login_failed

from mpframework.common import log
from mpframework.common.form import parsleyfy

from ..models import mpUser


@parsleyfy
class mpAuthenticationForm( AuthenticationForm ):
    """
    Override Django login form to add support for multitenancy,
    "remember me", and more control over authentication in general.

    Validity of email is checked, but no additional error handling is added
    to this form (e.g., parsley check on password length)
    and any kind of error is mapped to an authentication error
    to prevent information leakage during probing.
    """
    error_messages = dict( AuthenticationForm.error_messages, **{
            'authenticate': u"That username or password is not recognized",
            'login_code': u"The required code is not valid",
            'inactive': u"Your account is inactive, please contact support.",
            })

    # Email used both to contact user, as unique visible name and
    # as the basis for the hidden multitenant username
    email = forms.EmailField( widget=forms.EmailInput( attrs={'autocomplete': 'email'} ) )

    # User-controlled session length
    remember = forms.BooleanField( initial=True, required=False )

    # This is expected by Django processing that uses this form, it is
    # not collected directly from user
    username = forms.CharField( required=False )

    # Optional code used in some scenarios
    login_code = forms.CharField( required=False )

    def __init__( self, sandbox, *args, **kwargs ):
        self.required_code = kwargs.pop( 'login_code', None )
        super().__init__( *args, **kwargs )
        self.sandbox = sandbox

    def clean( self ):
        """
        Override Django Authentication with multitenant user
        """
        email = self.cleaned_data.get('email')
        user = mpUser.objects.get_user_from_email( email, self.sandbox )

        if user:
            password = self.cleaned_data.get('password')
            if password:
                log.info2("Authenticating: %s -> %s (%s)", self.sandbox, user, email)
                self.user_cache = authenticate( user=user, password=password )
                if self.user_cache:
                    if user.is_active:
                        self.cleaned_data['username'] = self.user_cache.email
                        return self.cleaned_data

        user_login_failed.send( sender=self.__class__, credentials={ 'username': email } )
        error = self.error_messages.get( 'inactive' if user and not user.is_active
                                            else 'authenticate' )
        raise forms.ValidationError( error )

    def clean_login_code( self ):
        """
        If no code is needed, both field and the value blank so will be equal
        """
        if self.required_code and self.required_code != self.cleaned_data.get('login_code'):
            log.info("Invalid login user code: %s", self.error_messages.get('login_code'))
            raise forms.ValidationError( self.error_messages.get('login_code') )

