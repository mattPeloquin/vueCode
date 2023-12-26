/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Shared prototype behavior for VM and VM bags
*/
(function() { 'use strict';

    mpp.VmShared = function( values ) {
    /*
        Base constructor that can also be used to create
        VM placeholder objects for navigation.
    */
        const self = Object.create( mpp.VmShared.prototype )
        _.extend( self, {
            id: 0,
            name: '',
            slug: '',
            model: {},
            }, values || {} )
        return self
        }
    mpp.VmShared.prototype = {

        accessor_ko: function( accessor_name, fn_or_val ) {
        /*
            Factory for lazy KO observable VM subsets.
        */
            return this.accessor( accessor_name, fn_or_val,
                        ko.observableArray, { notify: 'always' } )
            },

        accessor: function( accessor_name, fn_or_val,
                    observable_wrapper, observable_extend ) {
        /*
            Factory to lazily create subsets of Models or VMs.
            Generated accessor function RETURNS A JS ARRAY, which is
            what fn_or_val is expected to return.
            The generated accessor caches result if no args to fn.
        */
            if( this.accessor_name ) {
                mp.log_info("ACCESSOR ALREADY EXISTS: ", accessor_name,
                    this, fn_or_val)
                return
                }
            const self = this
            const cache_name = '__' + accessor_name
            self[ cache_name ] = false

            // Accessor can have arguments passed from template,
            // don't cache results in that case
            const accessor_fn = function( arg ) {
                let rv = []
                // Get new set of values
                if( arg || self[ cache_name ] === false ) {
                    const values = typeof fn_or_val === "function" ?
                                fn_or_val( arg ) : fn_or_val
                    // Update existing object values if observable
                    if( observable_wrapper ) {
                        rv = observable_wrapper( values )
                        if( observable_extend ) {
                            rv.extend( observable_extend )
                            }
                        }
                    else {
                        rv = values
                        }
                    }
                // Otherwise use cached values
                else {
                    rv = self[ cache_name ]
                    }
                arg || ( self[ cache_name ] = rv )
                return rv
                }

            self[ accessor_name ] = accessor_fn
            },

        /*
            Get any SiteBuilder options, starting with our VM
        */
        sb_option: function( name, element ) {
            return mpp.sb_option( name, element, this )
            },
        sbt: function( name, element ) {
            return mpp.sbt( name, element, this )
            },

        get_slug: function() {
        /*
            Support faux VMs that don't have models, which set slug
            directly (e.g., bags for panels).
        */
            if( this.slug === undefined ) {
                this.slug = this.model.get('slug')
                }
            return this.slug
            },

        navigate_init: function( panel ) {
        /*
            Placeholder for processing when navigated to
        */
            },

        logname: function() {
            // Override in derived classes
            mp.debugger()
            },
        }

    })();
