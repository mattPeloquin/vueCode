#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Signals related to user
"""
from django.dispatch import Signal


mpuser_created = Signal()
mpuser_activated = Signal()
mpuser_invalidate = Signal()

mpuser_health_check = Signal()
