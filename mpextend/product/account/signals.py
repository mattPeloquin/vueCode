#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Account signals
"""
from django.dispatch import Signal


# Notify apa has been updated
apa_update = Signal()
apa_add_users = Signal()
