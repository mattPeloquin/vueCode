#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Cross-app events
"""
from django.dispatch import Signal


# Signal that app models are loaded
startup_signal = Signal()
