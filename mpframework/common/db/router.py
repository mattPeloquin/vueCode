#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    DB routing placeholder - MPF does not use Django DB routing

    It was prototyped for use on a per-app basis, but decided to use
    using() to designate read replica use in specific situations.
    This provides better granularity, makes the code clearer, and
    works around issues seen with (earlier) Django trying to make
    DB calls sticky and not honoring db_for_write.
"""

class DbRouter:

    def db_for_read( self, model, **hints ):
        return 'default'

    def db_for_write( self, model, **hints ):
        return 'default'

    def allow_relation( self, obj1, obj2, **hints ):
        return True

    def allow_migrate( self, db, app_label, model=None, **hints ):
        return True
