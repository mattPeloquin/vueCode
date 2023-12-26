#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    mpUser creation
"""
from django import forms
from django.forms.forms import NON_FIELD_ERRORS
from django.forms.utils import ErrorDict

from mpframework.common import log
from mpframework.common import constants as mc

from ..models import mpUser
from .password import SetPasswordForm


class mpUsernameBaseFormMixin:
    """
    Reusable code for validating whether an email exists in forms
    Derived class must call set_sandbox
    """
    error_messages = {
        'email_inuse':  u"That email is already in use",
        }

    def set_sandbox( self, sandbox ):
        """
        Stash the sandbox
        """
        self.sandbox = sandbox

    def set_user_exists_error( self ):
        """
        Since check for existence can be part of the create_user flow, support returning
        the user exists error on this form
        """
        self._errors[NON_FIELD_ERRORS] = self.error_messages.get('email_inuse')

    def validate_email( self, email ):
        """
        Throw exception if email is already used related to this sandbox
        """
        user = mpUser.objects.get_user_from_email( email, self.sandbox )
        if user:
            log.info2("Email exists for sandbox/provider staff: %s -> %s, %s",
                        email, self.sandbox, user)
            raise forms.ValidationError( self.error_messages.get('email_inuse') )

        log.debug2("User %s does not exist yet, ok to use", email)


#-------------------------------------------------------------------------
class CreateUserBaseForm( SetPasswordForm ):
    """
    Shared code for creating a user in the framework.
    Can't leverage the Django user creation form since framework
    has a custom user model

    This only deals with a small subset of the mpUser model, so
    doesn't really need to be a form model, but for now keeping
    it that way as a convenience.

    DO NOT check if email exists here, to support logging in
    user if they used the create form by accident.
    """
    error_messages = dict( SetPasswordForm.error_messages, **{
            'create_code': "The required code is not valid",
            'honeypot': "Success", # Fake message, never seen by a user
            })

    email = forms.EmailField( max_length=mc.CHAR_LEN_UI_EMAIL,
                    widget=forms.EmailInput( attrs={'autocomplete': 'off'} ) )

    # Optional code needed to create user in specific contexts
    create_code = forms.CharField( required=False )

    # Term acceptance can be offered on some screens
    accept_terms = forms.BooleanField( required=False )

    # Simple honeypot to fool dumb bots into filling it out
    # Unfortunately with changes in browser autofill, using 'name', etc. is risky
    # because the browser may fill it
    code1 = forms.CharField( required=False )

    def __init__( self, *args, **kwargs ):

        # Get any access code that needs to be validated
        self.required_code = kwargs.pop( 'create_code', None )

        # HACK - pass none as fist argument, as SetPasswordForm expects user
        # This allows use of shared password form for new user and change password
        super().__init__( None, *args, **kwargs )


    def full_clean(self):
        """
        DJANGO OVERRIDE

        It's unusual to override full_clean, but needed some checks before fields are
        validated, while still keeping logic encapsulated in the form.

        Unfortunately, Django wasn't setup to hook this case, so since adding
        errors to self_errors, need to define it and then do the remainder
        of full_clean() behavior here.
        """
        self._errors = ErrorDict()
        if not self.is_bound: # Stop further processing.
            return

        # Make sure the honeypot is empty
        honeypot = self.fields['code1']
        honeypot_contents = honeypot.widget.value_from_datadict( self.data, self.files, self.add_prefix('name') )
        if honeypot_contents:
            log.warning("SUSPECT ATTACK - User Create honey pot: %s", honeypot_contents)
            self._errors[NON_FIELD_ERRORS] = self.error_messages.get('honeypot')
            return

        # Run the rest of form validation
        self.cleaned_data = {}
        # If the form is permitted to be empty, and none of the form data has
        # changed from the initial data, short circuit any validation.
        if self.empty_permitted and not self.has_changed():
            return
        self._clean_fields()
        self._clean_form()
        self._post_clean()

        self.errors and log.debug("Create User errors: %s", self.errors)

    def clean_create_code( self ):
        """
        If no code is needed, both field and the value blank so will be equal
        """
        if self.required_code and self.required_code != self.cleaned_data.get('create_code'):
            log.info("Invalid create user code: %s", self.error_messages.get('create_code'))
            raise forms.ValidationError( self.error_messages.get('create_code') )


#-------------------------------------------------------------------------
class mpUserCreationForm( mpUsernameBaseFormMixin, CreateUserBaseForm ):
    """
    Can't leverage the Django user creation form since framework
    has a custom user model

    This only deals with a small subset of the mpUser model, so
    doesn't really need to be a form model, but for now keeping
    it that way as a convenience.
    """
    error_messages = dict( CreateUserBaseForm.error_messages,
            **dict( mpUsernameBaseFormMixin.error_messages,
            **{
            }))

    # Optional information that might be on template
    first_name = forms.CharField( required=False )
    last_name = forms.CharField( required=False )
    organization = forms.CharField( required=False )
    title = forms.CharField( required=False )

    # Items that can potentially be shown on template or updated
    # through user request querystrings
    postal_code = forms.CharField( required=False )
    country = forms.CharField( required=False )
    external_key = forms.CharField( required=False )
    external_group = forms.CharField( required=False )
    external_tag = forms.CharField( required=False )
    external_tag2 = forms.CharField( required=False )
    external_tag3 = forms.CharField( required=False )

    def __init__( self, sandbox, *args, **kwargs ):

        # Stash sandbox for user validation
        self.set_sandbox( sandbox )

        # Add prefix to auto_id to separate create form from existing login form
        kwargs['auto_id'] = 'new_%s'

        super().__init__( *args, **kwargs )


    def add_prefix(self, field_name):
        """
        HACK -- taking over add_prefix as handy place to map the UserCreationForm's
        username field onto the new_user name we want to use.
        """
        FIELD_NAME_MAPPING = { 'email': 'new_user' }
        field_name = FIELD_NAME_MAPPING.get( field_name, field_name )
        return super().add_prefix( field_name )
