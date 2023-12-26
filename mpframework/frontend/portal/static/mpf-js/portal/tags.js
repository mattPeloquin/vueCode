/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Tag case-insensitive and wildcard matching logic

    Recreate most of the content tag matching logic from the
    server, to provide UI display using info available on the client.
*/
(function() { 'use strict';

    const NEGATION_DELIM = '!'
    const REGEX_DELIM = '/'

    mpp.tag_match_item = function( item, tags, nodes ) {
    /*
        Return whether any tags matches the item model's tag
        Optionally check any items in nodes (e.g., root collections).
    */
        let match = false
        const item_tag = item.get('tag') ? item.get('tag').toLowerCase() : ''
        if( tags ) {
            tags = (tags + '').split(',')
            // Check item first
            if( item_tag ) {
                _.some( tags, function( tag ) {
                    match = _tag_match( tag, item_tag )
                    return match
                    })
                }
            // Check any trees the item is part of
            if( !match && nodes ) {
                _.some( nodes, function( node ) {
                    match = mpp.tag_match_item( node, tags )
                    return match
                    })
                }
            }
        return match
        }

    function _tag_match( tag, item_tag ) {
    /*
        Replicate mpframework.common.tags matching logic.
        Duplicating logic isn't ideal, but this is easiest way.
    */
        if( !tag ) {
            return false
            }
        // Check exact match
        tag = tag.toLowerCase()
        if( tag == item_tag ) {
            return true
            }

        // Setup for one return with negation
        let rv = false
        let negative = false
        if( _.startsWith( tag, NEGATION_DELIM ) ) {
            negative = true
            tag = _.trim( tag, NEGATION_DELIM )
            }

        // Regular expression
        if( _.startsWith( tag, REGEX_DELIM ) ) {
            try {
                rv = RegExp( _.replace( tag, REGEX_DELIM, '' ) ).test( item_tag )
            }
            catch( e ) {
                mp.log_error("Bad regex tag match: ", tag, " -> ", e)
                }
            }

        // Wildcards
        if( !rv ) {
            const text = _.trim( tag, '*' )
            const frags = text.split('*')
            // Wildcards in the middle
            if( frags.length > 1 ) {
                rv = frags.every( function( frag ) {
                    if( _.includes( item_tag, frag ) ) {
                        item_tag = _.replace( item_tag, frag, '' )
                        return true
                        }
                    })
                }
            // Wildcards on the ends
            else if( _.startsWith( tag, '*' ) && _.endsWith( tag, '*' ) ) {
                rv = _.includes( item_tag, text )
                }
            else if( _.startsWith( tag, '*' ) ) {
                rv = _.endsWith( item_tag, text )
                }
            else if( _.endsWith( tag, '*' ) ) {
                rv = _.startsWith( item_tag, text )
                }
            }

        return !!rv != negative
        }

    })();
