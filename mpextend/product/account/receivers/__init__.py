#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Register account receivers that sync account state
    with other app events
"""

from .save import handle_mpuser_post_save
from .save import handle_mpuser_invalidate
from .health import handle_mpuser_health_check
