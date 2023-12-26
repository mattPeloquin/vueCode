#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Supporting shared catalog logic
"""

from mpframework.common import log
from mpframework.common.cache import cache_rv

from .cache import cache_group_catalog


@cache_rv( group=cache_group_catalog )
def free_pa_content( sandbox_id ):
    """
    Helper for optimizing detecting content tied to "free" PAs.

    Returns item ids that both:
      - Allow trial usage
      - Connect to PAs with no price, visible to all, and set to not prompt

    Does NOT ADD INDIVIDUAL ITEMS that are inside free collections; those
    should be picked up in access scenarios by the free collection.
    """
    from .models import PA
    rv = []
    pas = PA.objects.get_available_pas( sandbox_id, _unit_price=0, visibility='A' )
    for pa in pas:
        if pa.rules['no_prompt']:
            rv.extend( pa.content_dict(
                        sb_options__icontains='no_trials: true' )['all_ids'] )
    rv = list( dict.fromkeys( rv ) )
    log.debug("Caching free content: %s -> %s", sandbox_id, rv)
    return rv

@cache_rv( group=cache_group_catalog )
def public_pas( sandbox_id ):
    """
    Optimize lookup of PAs publicly available in a sandbox
    """
    from .models import PA
    pas = PA.objects.get_available_pas( sandbox_id, visibility='A' )
    rv = list( pas )
    log.debug("Caching public PAs: %s -> %s", sandbox_id, rv)
    return rv
