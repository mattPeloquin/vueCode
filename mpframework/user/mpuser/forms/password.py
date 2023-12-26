#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Override default Django password forms
"""
import re
from django import forms
from django.conf import settings
from django.contrib.auth.forms import PasswordResetForm

from mpframework.common import log
from mpframework.common.email import send_email_user
from mpframework.common.cache import stash_method_rv
from mpframework.common.form import BaseForm
from mpframework.common.form import parsleyfy

from ..models import mpUser


# Password policy searches
_RE_ONE_NON_LETTER = '[^a-zA-Z]{1}'
_re_all_letters = re.compile('^[a-zA-Z]+$')


@parsleyfy
class ResetPasswordForm( PasswordResetForm ):
    """
    Add parsley to built-in Django form.
    """

    def __init__( self, data=None, *args, **kwargs ):
        super().__init__( data, *args, **kwargs )
        self.sandbox = data.get('sandbox') if data else None

    def clean_email( self ):
        email = self.cleaned_data['email']
        user = self._get_user( email )
        if not user:
            raise forms.ValidationError(
                    u"We have no record of a user with the email: {}".format(email))
        return email

    def get_users( self, email ):
        """
        Returns one user if valid, but in list as expected by base save
        """
        rv = ()
        user = self._get_user( email )
        if user and user.is_active:
            log.debug("Password reset valid user: %s -> %s", self.sandbox, email)
            rv = ( user ,)
        else:
            log.info("Password reset invalid user: %s -> %s", self.sandbox, email)
        return rv

    @stash_method_rv
    def _get_user( self, email ):
        assert self.sandbox
        if self.sandbox:
            return mpUser.objects.get_user_from_email( email, self.sandbox )

    def save( self, *args, **kwargs ):
        """
        Setup sandbox for get_users that will be called by default save
        """
        request = kwargs.get('request')
        if request:
            self.sandbox = request.sandbox

            kwargs['from_email'] = self.sandbox.email_support
            kwargs['extra_email_context'] = { 'site': self.sandbox }

        super().save( *args, **kwargs )


#-------------------------------------------------------------------------
class SetPasswordForm( BaseForm ):
    """
    Base form that supports new password behavior

    Used both in MPF and passed to Django as replacement for SetPasswordForm.

    Adds parsley password support for new passwords, and makes password
    failures form failures (most cases should be caught on client)
    """
    error_messages = {
        'len-letters': "At least {} chars, one that isn't a letter".format(settings.MP_PASSWORD_MIN_LEN),
        'mismatch': "Passwords do not match",
        'length':   "Passwords need at least {} characters".format(settings.MP_PASSWORD_MIN_LEN),
        'username': "The requested password is too similar to your email",
        'invalid': "The password contains a word that is too easily guessed",
        'chars': "The requested password needs more character diversity",
        'letters': "Passwords need more than just letters",
        }

    # The main password field is always used
    password1 = forms.CharField( widget=forms.PasswordInput(attrs={'autocomplete': 'off'}) )

    # To support optional password confirmation, this field is not required and only used
    # if shown on the client side (JS will force it to be used if it is shown)
    password2 = forms.CharField( widget=forms.PasswordInput(attrs={'autocomplete': 'off'}), required=False )

    # Add parsley client-side validation
    # Message fields used for each field's errors is limited to make UI layout
    # easier because parsley messages don't stack up and cause movement
    parsley_extras = {
        'password1': {
            'minlength': settings.MP_PASSWORD_MIN_LEN,
            'regexp': _RE_ONE_NON_LETTER,
            'error-message': error_messages['len-letters'],
            },
        'password2': {
            'equalto': "password1",
            'error-message': error_messages.get('mismatch'),
            },
        }

    def __init__( self, user, *args, **kwargs ):
        """
        Match the init signature of Django's SetPasswordForm; in some
        cases where used in the framework, user will be empty
        """
        self.user = user
        super().__init__( *args, **kwargs )

    def save( self, commit=True ):
        """
        Save new password in the derived model.
        User must be set to call this
        """
        user = self.user
        assert user

        user.set_password( self.cleaned_data.get('password1') )

        if commit:
            log.debug2("Sending password changed email for: %s", user)
            user.save()

            context = {
                'user': user,
                'site_name': user.sandbox,
                }

            send_email_user( user, 'user/password/changed_email.html', context )

        return user

    def clean_password2(self):
        """
        Enforce password policy through checks on password2 to make
        sure if confirmation fails it fails before other checks.
        All errors raise exception to be treated as form errors.
        """

        # Get values, use defaults to handle empty cases
        password1 = self.cleaned_data.get( 'password1', '_bad_' )
        password2 = self.cleaned_data.get( 'password2', '' )

        # Make password confirmation failure a form error
        if password2 and password1 != password2:
            raise forms.ValidationError( self.error_messages.get('mismatch') )

        # Now actually validate using password1
        pwd = password1.lower()

        # Ensure length
        if len(pwd) < settings.MP_PASSWORD_MIN_LEN:
            raise forms.ValidationError( self.error_messages.get('length') )

        # Must have at least some different chars; don't go nuts here
        if pwd.count( pwd[0] ) > (len(pwd) // 2 ):
            raise forms.ValidationError( self.error_messages.get('chars') )

        # Doing only letters vs. requiring specific numbers, etc.
        if _re_all_letters.match( pwd ):
            raise forms.ValidationError( self.error_messages.get('letters') )

        # Cannot have fragment from banned list
        if any(text in pwd for text in settings.MP_PASSWORD_INVALID):
            raise forms.ValidationError( self.error_messages.get('invalid') )

        # If email is available, don't allow password that is part of username
        email = self.user.email if self.user else ''
        if email:
            email = email.lower()
            if pwd in email or email in pwd:
                raise forms.ValidationError( self.error_messages.get('username') )


#-------------------------------------------------------------------------
class ChangePasswordForm(SetPasswordForm):
    """
    Adds verification of old password when changing passwords
    """
    error_messages = dict(SetPasswordForm.error_messages, **{
        'old_incorrect': "Old password does not match our records",
        })

    old_password = forms.CharField( widget=forms.PasswordInput )

    def clean_old_password(self):
        old_password = self.cleaned_data.get( 'old_password' )
        if not self.user.check_password( old_password ):
            raise forms.ValidationError( self.error_messages.get('old_incorrect') )
        return old_password

