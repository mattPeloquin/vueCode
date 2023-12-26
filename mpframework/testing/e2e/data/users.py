#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    System test data templates for users
"""

USERS = {

    'BOB': {
        'email': 'bob{ascii}@vueocity.com',
        'password': 'mptest1',
        'first_name': 'Bob',
        'last_name': '{}',
        'company': 'Acme {}',
        'user_report_tag': 'tag{}',
        'Occupation': 'Web Developer',
        'comments': 'Comment {txt}',
        },

    'ALICE': {
        'email': 'alice{ascii}@vueocity.com',
        'password': '!@#$%^!!12375_long_!!! for Alice',
        'first_name': 'Alice',
        'last_name': '{}',
        },

    }

STAFF = {

    # This is the template for new site owner

    'SBPRO': {
        'first_level': 'SiteBuilder Pro',
        'email': 'sbpro{ascii}@vueocity.com',
        'password': 'mptest1',
        'first_name': 'SBPro',
        'last_name': '{}',
        'company': 'vue{}',
        'vueocity_account_manager': 'yes',
        'vueocity_account_owner': 'yes',
        },

    # These staff are can get created through new_staff user story

    'SB': {
        'first_level': 'SiteBuilder',
        'email': 'sb{ascii}@vueocity.com',
        'password': 'mptest1',
        'first_name': 'SB',
        'last_name': '{}',
        'name': 'Staff SB {}',
        'vueocity_account_manager': 'yes',
        'vueocity_account_owner': 'no',
        },
    'EASY': {
        'first_level': 'EasyVue',
        'email': 'easy{ascii}@vueocity.com',
        'password': 'mptest1',
        'first_name': 'EasyVue',
        'last_name': '{}',
        'name': 'Staff Easy {}',
        },
    }
