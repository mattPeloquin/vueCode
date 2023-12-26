#--- Vueocity platform, Copyright 2021 Vueocity LLC
"""
    Override mpUser with Account behaviors

    Monkey-patching the mpUser class is used here to support mpExtend
    adaptions to behavior without additional code.
"""

from mpframework.common.cache import stash_method_rv
from mpframework.user.mpuser.models import mpUser
from mpextend.product.account.utils import get_au


@property
@stash_method_rv
def _au( self ):
    """
    Provide stashed AU access in mpExtend
    """
    return None if self.is_staff else get_au( self )

mpUser.au = _au


def _cache_extend( self ):
    """
    Support extensions adding/stashing info to user object before cache
    """
    if self.au:
        self.au.delivery_mode
        self.au.is_group_admin()

mpUser._cache_extend = _cache_extend


def _delivery_mode( self, default=None ):
    if self._delivery_mode:
        return self._delivery_mode
    if self.au and self.au.delivery_mode:
        return self.au.delivery_mode
    return default if default else self.sandbox.delivery_mode

mpUser.delivery_mode = _delivery_mode


@property
def _workflow_filters( self ):
    rv = ['P']
    if self.is_ready():
        rv.append('Q')
        if self.workflow_level >= self.WFL_BETA or (
                    self.au and self.au.beta_access ):
            rv.append('B')
        if self.workflow_dev:
            rv.append('D')
    return rv

mpUser.workflow_filters = _workflow_filters


@property
@stash_method_rv
def _use_compat_urls( self ):
    if self.options['use_compat_urls']:
        return True
    if self.au and self.au.options and self.au.options['use_compat_urls']:
        return True
    return self.sandbox.options['use_compat_urls']

mpUser.use_compat_urls = _use_compat_urls
