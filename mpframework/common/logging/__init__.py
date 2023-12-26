#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    MPF logging extensions (see common.log for more detail)

    Imports from other common modules in logging modules are done inline to
    avoid circular loading dependencies.
"""

# Register MPF logger as default logger
import logging
from .logger import mpLogger
logging.setLoggerClass( mpLogger )
