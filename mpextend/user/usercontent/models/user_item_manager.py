#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Manager for user items
"""

from mpframework.common import log
from mpframework.foundation.tenant.models.base import TenantManager


class UserItemManager( TenantManager ):

    def get_user_item( self, cu, item, create=False, **kwargs ):
        """
        Get UserItem for the user/contentuser, trying to create if doesn't exist.
        item must be a Content item or item id.
        Due to lazy creation of records, race conditions on creating the
        record can exist, so try to get twice with a create attempt in between.
        """
        from . import ContentUser
        assert item
        log.debug2("get_user_item: %s -> %s", cu, item)

        # Passed user or contentuser?
        if not isinstance( cu, ContentUser ):
            cu = ContentUser.objects.get_contentuser( cu )

        # Don't create content records if no cu (e.g., root accounts, opt-outs)
        if not cu:
            return

        # Passed item object or id?
        if isinstance( item, (int, str) ):
            item_id = int( item )
            version = 0
        else:
            item_id = item.pk
            version = item.version

        # Try to get or create, using only master to
        # lower chance of race conditions
        if cu:
            try:
                try:
                    return self.get( cu=cu, item_id=item_id, **kwargs )

                except self.model.DoesNotExist:
                    if create:
                        try:
                            # Create the user item
                            cui = self.model( sandbox=cu.sandbox, cu=cu,
                                                item_id=item_id, item_version=version )
                            cui.save()
                            log.info3("Created user_item: %s", cui)
                        except Exception as e:
                            # FUTURE - if conflicts happen often, reduce creation contention
                            log.info2("Error creating user_item: %s, %s -> %s: %s",
                                        cu, item_id, type(e), e)

                        # Try last time, in case another request created
                        return self.get( cu=cu, item_id=item_id, **kwargs )

            except Exception as e:
                log.info("Exception get/create user_item: %s, %s -> %s", cu, item_id, e)
                raise
