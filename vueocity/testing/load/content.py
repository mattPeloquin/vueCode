#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared load test code for managing content on sites
"""
import json
import random

from .utils import get_from_dict


class PortalContent:
    """
    Given the JSON from portal bootstrap, provides enough simulation of the
    portal application to support making load test calls
    """
    def __init__( self, locust, bootstrap ):
        self.locust = locust
        self.items = bootstrap['items']
        self.trees = bootstrap['trees']

    @property
    def get_random_item( self ):
        return self.items[ random.randint( 0, len(self.items) - 1 ) ]

    def access_item( self, id=None ):
        """
        Simulate client access for both staff and user
        """
        id = id or self.get_random_item['id']
        info = None

        # Make the initial request
        access = self.locust.post( '/api/public/uc/item_access', {
            'id': id,
            }, ajax=True )
        if access.ok:
            try:
                info = access.json()
                info = info and info.get('values')
            except ValueError:
                print("item_access BAD CONTENT", self.locust.name, id, access.text)
                return

        if not info:
            print("item_access FAIL", self.locust.name, id, access)
            return

        # Client sends a usage state on first request
        self.send_item_state( id )

        # Check whether access is already provided
        access_url = info.get('access_url')

        # Otherwise, make request for access session
        if not access_url:
            accounts = json.loads( info['accounts'] )
            account = None
            if accounts:
                account = json.loads( get_from_dict( accounts ) )
            pas = json.loads( info['pas'] )
            pa = None
            if pas:
                pa = json.loads( get_from_dict( pas ) )

            select_pa = self.locust.post( '/user/account/access_select', {
                'pa_id': pa['id'] if pa else '',
                'account_id': account['id'] if account else '',
                'coupon_code': '',
                'country': 'LoadTest',
                'postal_code': 'LoadTest',
                })
            if not select_pa.ok:
                print("new_license request FAIL", self.locust.name, id, select_pa)
                return

            try:
                access_url = select_pa.json().get('values').get('access_url')
            except ValueError:
                print("new_license request PAY CANCEL", self.locust.name, id)
                return

        if access_url:
            url = self.locust.get( access_url, 'ACCESS' )
            if url.ok:
                return id

        print("access FAIL", self.locust.name, id)

    def send_item_state( self, id, progress='', status='' ):
        data = {
            'id': id,
            'progress': progress,
            'status': status,
            }
        response = self.locust.patch( '/api/uc/user_items/' + str(id),
                                            json.dumps( data ))
        print("SEND ITEM STATE", self.locust.name, data, response)
        return response

