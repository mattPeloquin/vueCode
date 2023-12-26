#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Global constants
"""

"""-------------------------------------------------------------------
    Staff Access Level values

    Defines linear access model for use in Admin, template code, and logic to:

     - Define users as staff
     - Determine what users can see in UI
     - When needed, validates requests on the server

    The goal is a flexible, simple role definition for both direct users,
    and for providers who resell to customers.
    Greater values indicate more privilege
"""
STAFF_LEVEL_NONE = 0

STAFF_LEVEL_RO = 1
STAFF_LEVEL_LOW = 10
STAFF_LEVEL_MED = 30
STAFF_LEVEL_HIGH = 50
STAFF_LEVEL_ALL = 70

# Root functionality levels (expose different amounts of menu)
STAFF_LEVEL_ROOT = 90
STAFF_LEVEL_ROOT_MENU = 95
STAFF_LEVEL_ROOT_ALL = 99


"""-------------------------------------------------------------------
    Char field, max lengths, and truncation

    In Django CharField length isn't about DB optimization, as every CharField
    is stored a varchar -- rather it is about default form validation. This
    is because of Django's focus on char's coming from forms.

    There are places where MPF has char fields that sometimes
    or all the time may not be populated through forms. This can lead to
    unexpected exceptions when writing to a real DB (but not SqlLite)
"""

# Large char fields can be DB searched unlike TextFields,
# but place a limit to avoid search performance issues
CHAR_LEN_DB_SEARCH = 8192

# Standardized UI lengths based on UI display design
CHAR_LEN_UI_CODE = 32
CHAR_LEN_UI_DEFAULT = 64
CHAR_LEN_UI_LINE = 96
CHAR_LEN_UI_EMAIL = 75
CHAR_LEN_UI_SHORT = 48
CHAR_LEN_UI_WIDE = 92
CHAR_LEN_UI_LONG = 255      # Longest for MySQL unique columns
CHAR_LEN_UI_BLURB = 512

UI_TEXT_SIZE_CODE = { 'size': 32 }
UI_TEXT_SIZE_DEFAULT = { 'size': 64 }
UI_TEXT_SIZE_LARGE = { 'size': 80 }
UI_TEXT_SIZE_XLARGE = { 'size': 120 }

UI_TEXTAREA_DEFAULT = { 'rows': 2, 'cols': CHAR_LEN_UI_DEFAULT }
UI_TEXTAREA_SMALL = { 'rows': 3, 'cols': CHAR_LEN_UI_SHORT }
UI_TEXTAREA_LARGE = { 'rows': 4, 'cols': CHAR_LEN_UI_DEFAULT }

# Put limits on open text field lengths either for UI design or to prevent attack
TEXT_LEN_SMALL = 8192
TEXT_LEN_MED = 32768
TEXT_LEN_LARGE = 131072

# Other standardized lengths
CHAR_LEN_PATH = 255
CHAR_LEN_IP = 48
