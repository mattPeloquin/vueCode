#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Payment finish pages
"""

from mpframework.common import log

from ..payment_types import PAYMENT_TYPES


def payment_finish( request, paytype ):
    pt = PAYMENT_TYPES[ paytype ]
    log.info2("PAYMENT FINISHED: %s, %s", request.mpname, pt['name'])

    return pt['flow'].finish.flow_end( request )
