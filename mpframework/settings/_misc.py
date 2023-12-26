#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Settings for misc items

    DESIGNED TO BE * IMPORTED BY settings.__init__.py
"""

from . import env


# System options that can be set in the root UI
# OPTIONS HAVE PLAYPEN SCOPE - so although defaults can be modified in
# profiles, they can't be tuned across profiles that share a playpen
# (prod-mpd is an exception)
MP_OPTIONS = [
    # Feature flag defaults
    ('flags', env.MP_FLAGS ),
    # Tuning options baked into TuningForm or BanForm
    ('disable_non_critical', env.MP_TUNING['DISABLE_NON_CRITICAL'] ),
    ('throttle_period', env.MP_TUNING['THROTTLE']['PERIOD'] ),
    ('throttle_thresh', env.MP_TUNING['THROTTLE']['THRESHOLD'] ),
    ('throttle_thresh_boost', env.MP_TUNING['THROTTLE']['THRESHOLD_BOOST'] ),
    ('throttle_exempt', env.MP_TUNING['THROTTLE'].get('EXEMPT', []) ),
    ('warn_seconds', env.MP_TUNING['THROTTLE']['WARN_SECONDS'] ),
    ('ban_threshold', env.MP_TUNING['THROTTLE']['BAN_THRESHOLD'] ),
    ('ban_seconds', env.MP_TUNING['THROTTLE']['BAN_SECONDS'] ),
    # Dynamic integer values
    ('client_ping', env.MP_TUNING['CLIENT_PING_FREQUENCY'],
        "Seconds between client pings/updates"),
    ]

#--------------------------------------------------------------------
# Django add-ons

# Don't have Saas processor look in app subfolders because it tries
# to use storages base_url method that doesn't work with S3 storages
# And there's no static in apps in MPF anyway
SASS_PROCESSOR_AUTO_INCLUDE = False

# Admin indent for MPTT models
MPTT_ADMIN_LEVEL_INDENT = 12

# Subset of time zones that is manageable
# Include information for display, pytz, and offset minutes
MP_TIME_ZONES = (
    ('UTC', 'UTC', 0),
    ('US/Pacific', 'US/Pacific', 480 ),
    ('US/Mountain', 'US/Mountain', 420 ),
    ('US/Central', 'US/Central', 360),
    ('US/Eastern', 'US/Eastern', 300),
    ('Etc/GMT+1', 'GMT+1', -60),
    ('Etc/GMT+2', 'GMT+2', -120),
    ('Etc/GMT+3', 'GMT+3', -180),
    ('Etc/GMT+4', 'GMT+4', -240),
    ('Etc/GMT+5', 'GMT+5', -300),
    ('Etc/GMT+6', 'GMT+6', -360),
    ('Etc/GMT+7', 'GMT+7', -420),
    ('Etc/GMT+8', 'GMT+8', -480),
    ('Etc/GMT+9', 'GMT+9', -540),
    ('Etc/GMT+10', 'GMT+10', -600),
    ('Etc/GMT+11', 'GMT+11', -660),
    ('Etc/GMT+12', 'GMT+12', -720),
    ('Etc/GMT-1', 'GMT-1', 60),
    ('Etc/GMT-2', 'GMT-2', 120),
    ('Etc/GMT-3', 'GMT-3', 180),
    ('Etc/GMT-4', 'GMT-4', 240),
    ('Etc/GMT-5', 'GMT-5', 300),
    ('Etc/GMT-6', 'GMT-6', 360),
    ('Etc/GMT-7', 'GMT-7', 420),
    ('Etc/GMT-8', 'GMT-8', 480),
    ('Etc/GMT-9', 'GMT-9', 540),
    ('Etc/GMT-10', 'GMT-10', 600),
    ('Etc/GMT-11', 'GMT-11', 660),
    ('Etc/GMT-12', 'GMT-12', 720),
    )

