#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF SSO support

    Provides OAuth, OpenID, and SAML support for USER accounts
    (staff accounts not supported for now).

    Based on Cognito and setting up dedicated IDP apps
    in AWS for SAML group accounts, but abstracted enough to
    allow for other options in the future.
"""
