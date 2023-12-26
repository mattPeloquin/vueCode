/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Collection/Tree collection/bag
*/
(function() { 'use strict';

    /*---------------------------------------------------------------
        Tree bag
        All tree nodes are held in this bag, with added support
        for filtering roots.
     */
    mpp.Trees = mpp.ContentBag.extend({
        _bag_type: "Trees",
        model: mpp.Tree,

        roots: function( portal_group ) {
        /*
            Support root id optimization by caching root ids for filtering
            Assumes all trees are loaded before first call
        */
            portal_group = portal_group || ''
            const self = this
            if( !self._roots[ portal_group ] ) {
                self._roots[ portal_group ] = []
                this.forEach( function( node ) {
                    if( node.is_root() && (
                            !portal_group ||
                            node.get('portal_group') == portal_group ) ) {
                        self._roots[ portal_group ].push( node )
                        }
                    })
                }
            return self._roots[ portal_group ]
            },
        _roots: {},

        })

    })();
