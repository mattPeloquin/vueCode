/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Content access logic
*/
(function() { 'use strict';

    /*--------------------------------------------------------------
        Access Handlers

        Access handlers start an item access request based on content type.
        If the access request is successful, the delivery will be handled
        using the launcher from the request. If not, the access dialog is shown.
    */

    mpp.access_handlers_get = function( type ) {
        return mpp.access_handlers[ type ] || _default_handler
        }
    mpp.access_handlers = {}

    function _default_handler( item, node_id, launcher, direct_access ) {
        // Default handling is to delegate to the item
        return item.request_access( launcher, node_id, direct_access )
        }

    /*--------------------------------------------------------------
        Client-side access checks
        This of course is not the last word on access, so no concern
        if someone wanted to mess with it.
    */

    mpp.access_item = function( item ) {
    /*
        Return true if item model has general access, or APA tag if specific.
        Sets cached value in item for this session.
    */
        if( item.has_access !== undefined ) {
            return item.has_access
            }
        // Check various free cases
        let access = mp.user.access_staff || _access_site_free() ||
                    _access_item_free( item )
        // Then find the first APA that matches
        if( !access ) {
            _.some( mpp.access_apas, function( apa ) {
                if( _access_item_apa( item, apa ) ) {
                    access = apa
                    }
                return access
                })
            }
        item.has_access = access
        return access
        }

    function _access_site_free() {
        // Return true for any global free check
        if( _site_free === null ) {
            _site_free = mp.access_free_all ||
                    _.find( mpp.access_apas, function( apa ) {
                        return apa.tags.indexOf('*') >= 0
                        })
            }
        return _site_free
        }
    let _site_free = null

    function _access_item_free( item ) {
        // Is the item marked free in its or PA data?
        let free = mpp.access_free_items.indexOf( item.id ) >= 0 ||
                mpp.sb_option( 'access.free_public', '', item ) ||
                ( mp.user.is_ready && mpp.sb_option( 'access.free_user', '', item ) )
        // Check any trees the item is part of
        if( !free ) {
            _.some( item.roots(), function( root ) {
                free = _access_item_free( root )
                return free
                })
            }
        return free
        }

    function _access_item_apa( item, apa ) {
        // Skip no trial items
        if( apa.is_trial && item.sb_option('portal.no_trials') ) {
            return false
            }
        // If public or access already determined
        if( item.has_access ) {
            return item.has_access
            }
        // Finally return if there is an item tag match
        const access = mpp.tag_match_item( item, apa.tags, item.roots() )
        item.has_access = access
        return access
        }

    })();
