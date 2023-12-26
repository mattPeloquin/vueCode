/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Client-side SiteBuilder options, which are combined
    according to MPF's sitebuilder option hierarchy:

        1) VM/Model sb_options (if model available)
        2) Element context (if element available)
            2a) VM parents' sb_options for element $parents
            2b) Pane sb_options for the element
        3) Subset of site's sb_options (see mp.sb_options for site defaults)
*/
(function() { 'use strict';

    mpp.sb_option = function( name, element, item ) {
    /*
        Safely return sb_option for item vm or model or defaults
        for pane, portal, system.
        name is a dotted-name or array name for a SiteBuilder option,
        returns '' if option doesn't exist.
    */
        let rv = undefined
        // Check for pane overrides, which trump all to allow panes
        // to enforce consistent layout
        if( element ) {
            const pane = get_pane_context( element )
            rv = pane && _.get( pane.sb_options, name )
            }
        // Check for content overrides in vm/model
        if( ( rv === undefined ) && item && item.id ) {
            const model = item.model || item
            rv = model.sb_option( name )
            }
        // Check VM parents (parent based on HTML structure)
        if( ( rv === undefined ) && element ) {
            const context = ko.contextFor( element )
            if( context && context.$parents ) {
                context.$parents.some( function( parent ) {
                    rv = parent.model && parent.model.sb_option( name )
                    return !!rv
                    })
                }
            }
        // Check site's SB options sent to client
        if( rv === undefined ) {
            rv = _.get( mp.sb_options, name )
            }
        if( rv === undefined ) {
            rv = ''
            }
        return rv
        }

    mpp.sbt = function( name, element, item ) {
    /*
        For customizable text that can be updated in content, pane,
        or sandbox sb_options.
        Return text override or default.
    */
        let rv = ""
        try {
            rv = mpp.sb_option( 'text.' + name, element, item )
            if( !rv ) {
                rv = mpt[ name ]
                }
            }
        catch( e ) {
            mp.log_error("Exception getting text: ", name, e)
            }
        return rv
        }

    mpp.pane_options = function( name, element ) {
    /*
        Check current pane context for pane option
    */
        const pane = get_pane_context( element )
        return pane && _.get( pane.options, name )
        }

    function get_pane_context( element ) {
    /*
        Look for parent pane and get context from data.
        There should only be one pane deep, but use closest
        ancestor if there is a conflict.
        Pane context can either be injected in the frame structure
        for the pane, or via pane_sb_options from the pane template.
    */
        try {
            const pane = $( element ).parents("pane").addBack("pane").last()
            let pane_context = pane.data('pane_context')
            const options = pane.data('pane_sb_options')
            if( options ) {
                pane_context = pane_context || {}
                pane_context.sb_options = _.extend( options,
                        pane_context.sb_options || {} )
                }
            return pane_context
            }
        catch( e ) {
            mp.log_error("Exception getting pane context: ", e)
            }
        }

    })();
