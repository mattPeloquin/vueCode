#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Tenant signals
"""
from django.dispatch import Signal


# Signals indicating change in provider or sandbox
sandbox_change = Signal()
provider_change = Signal()
