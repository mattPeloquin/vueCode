/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    General user UI preferences stored in localStorage.
    Capture UI state that does not need to be sent back to the server
    in browser localStorage to increase usability and polish.
*/
(function() { 'use strict';

    mp.preference_store = function( selector, type, data, group ) {
    /*
        Call with unique selector for element(s), data to store,
        and group to place the data in. On initialize, the data
        is applied to selected elements according to type:
            toggle_hidden   data is a bool
            toggle_viz      data is a bool
            css             data is obj with jQuery css attrs
            class           List of { class:, on: } for classes to toggle on element
            class_closest   Same as class, but for closest parent
    */
        if( !selector || !type ) return
        const prefs = mp.preferences_get( group )
        prefs[ selector ] = {
            type: type,
            data: data,
            }
        _preferences_set( prefs, group )
        }

    mp.preferences_init = function( group ) {
    /*
        On startup, try to set preferences for any stored values
    */
        const prefs = mp.preferences_get( group )
        _.each( prefs, function( pref, selector, _list ) {
            mp.log_debug("Loading preference: ", selector, " -> ", pref)
            try {

                if( pref.type == 'toggle_hidden' ) {
                    $( selector ).toggleClass( 'mp_hidden', !pref.data )
                    }

                if( pref.type == 'toggle_viz' ) {
                    // Click the UI switch if area out of sync
                    const swtch = $( selector )
                    const area = mp.viz_find_area( swtch )
                    if( area && ( area.hasClass('mp_hidden') == pref.data ) ) {
                        swtch.trigger('click')
                        }
                    }

                if( pref.type == 'css' ) {
                    $( selector ).css( pref.data )
                    }

                if( pref.type == 'class' ) {
                    _.each( pref.data, function( toggle ) {
                        if( !toggle.class ) {
                            mp.log_info("Bad class preference: ", pref)
                            return
                            }
                        $( selector ).toggleClass( toggle.class, toggle.on )
                        })
                    }

                if( pref.type == 'class_closest' ) {
                    _.each( pref.data, function( toggle ) {
                        if( !toggle.closest ) {
                            mp.log_info("Bad class_closest preference: ", pref)
                            return
                            }
                        $( selector ).closest( toggle.closest ).
                            toggleClass( toggle.class, toggle.on )
                        })
                    }

                }
            catch( e ) {
                mp.log_info("Preferences exception: ", selector, " -> ", pref)
                mp.log_debug( e )
                }
            })
        }

    mp.preferences_get = function( group ) {
        return mp.local_get( _group( group ) )
        }

    mp.preferences_clear = function( group ) {
        _preferences_set( '', group )
        }

    function _group( group ) {
        group = 'preferences_' + ( group || 'site' )
        return group
        }

    function _preferences_set( prefs, group ) {
        return mp.local_set( _group( group ), prefs )
        }

    })();
