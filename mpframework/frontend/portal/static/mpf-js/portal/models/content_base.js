/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Portal base content model

    Content models represent content distilled by the server for a
    given portal session. They:
        - map onto JSON data provided by the server on a 1:1 basis
	    - are normally managed through model Bags (see bag.js)
        - back ViewModels, which are used for portal presentation

    They are Backbone models for viewing data and making small state changes,
    so they do not have a full REST API. Instead they are loaded from initial data,
    (through the heavily cached bootstrap process) and use specific AJAX calls
    to keep themselves in sync. Page reloads are used for major changes.
*/
(function() { 'use strict';

    // Getter/Setter for model typing, allows use of base mpp.Content class or
    // specialization registered based on type name
    mpp.model_types = function( type, model ) {
        mpp._model_types = mpp._model_types || {}
        if( model ) {
            mpp._model_types[ type ] = model
            }
        return mpp._model_types[ type ] || mpp.Content
        }

    /*--------------------------------------------------------------
        Base Content Model

        All content models extend this class, which takes advantage
        of the Backbone model for some of its ORM capability.

        The model data attributes are accessed in templates via
        ViewModels, and client-only attributes may be added to
        provide easy access in templates to data that needs
        basic logic to support fallback values.

        Backbone's class initialization pattern is used, so the items
        below are placed into the prototype.
    */
    mpp.Content = Backbone.Model.extend({

        urlRoot: mpurl.api_user_item,

        initialize: function() {
            mp.log_debug_level > 2 && mp.log_debug("CREATE", this.logname())

            // Initialize sorting
            this._set_natural_sort_hash({ silent: true })

            // Set derived values needed for filtering
            // Most setup of values should be done in lazy_init
            this._dynamic_defaults()
            },

        sb_option: function( name ) {
            try {
                return _.get( this.get('options'), name )
            } catch( e ) {
                mp.log_error("Error getting sb_option: ", name, "\n", e)
                }
            },

        roots: function() {
        /*
            Lazy cache list of any roots the item is associated with.
            If needed, this could be optimized with ID maps built up
            on the server and cached in browser bootstrap data.
        */
            const self = this
            if( !self._roots ) {
                self._roots = []
                mpp.models.trees.roots().forEach( function( root ) {
                    if( _.includes( root.all_children(), self.id ) ) {
                        self._roots.push( root )
                        }
                    if( _.includes( root.all_items(), self.id ) ) {
                        self._roots.push( root )
                        }
                    })
                }
            return self._roots
            },

        defaults: function() {
            return {
                // Values that won't be sent over wire if empty
                'tag': '',
                'slug': '',
                'workflow': 'P',
                'type_name': '',
                'type_view': '',
                'text1': '', 'text2': '',
                'image1': '', 'image2': '',
                'tooltip': '', 'text3': '', 'text4': '',
                'search_tags': '',
                'available': '',
                'options': {},
                // Values loaded on full load
                'hist_modified': '',
                'hist_rev': 1,
                // Internal state overridable by server
                'more_to_load': false,
                }
            },
        _urls: [ 'image1', 'image2' ],
        _lazy_attrs: [ 'hist_rev', 'hist_modified' ],

        _dynamic_defaults: function() {
            // Note if dynamic metadata exists, and if it has been loaded
            this.fully_loaded = !this.get('more_to_load')
            // Slug is here because it defaults to id and can be looked up
            // before model is full initialized
            this.set( 'slug', this.get('slug') || _.toString( this.id ) )
            },

        // Support lazy load of some attributes via ajax (if they exist)
        more_to_load: function( attr ) {
            return this.get('more_to_load') && this._lazy_attrs.indexOf( attr ) >= 0
            },

        load_full: function( fn ) {
        /*
            Default is lazy load of some metadata, this will get the rest
            fn is an optional completion callback.
        */
            const self = this
            mp.fetch({
                url: mpurl.api_content_full + self.id,
                finished: function( values ) {
                    mp.log_info("Dynamic model update: ", self)
                    self.lazy_init( values )
                    self.fully_loaded = true
                    // Call the callback if provided
                    fn && fn( self )
                    }
                })
            },

        lazy_init: function( values ) {
        /*
            Run initialization from data AND update values if needed.
        */
            if( values || !this.lazy_init_done ) {
                this._lazy_init( values )
                this.lazy_init_done = true
                }
            },
        _lazy_init: function( values ) {
            const self = this
            this.set( values )
            this._dynamic_defaults()

            // Does user currently have access?
            this.set( 'access', mpp.access_item( this ) )

            // Items with lookups or defaults to other properties
            this.set( 'type_name', this.get('type_name') || this.get('type_db') )
            this.set( 'type_view', this.get('type_view') || this.get('type_db') )

            // Convert text JSON into data
            if( this.get('hist_modified') ) {
                this.set( 'hist_modified', new Date( this.get('hist_modified') ) )
                }
            if( this.get('available') ) {
                this.set( 'available', new Date( this.get('available') ) )
                }

            // Fixup any urls for compatibility
            this._urls.forEach( function( field ) {
                self.set( field, mpurl.compat_url( self.get( field ) ) )
                })

            // Items only valid in production
            if( _.includes( mp.user.workflow, 'B' ) ) {
                if( this.sb_option('portal.coming_soon') ) {
                    let opts = this.get('options')
                    _.set( opts, 'portal.coming_soon', false )
                    this.set( 'options', opts )
                    }
                }
            },

        in_filter_groups: function( filter_groups ) {
        /*
            Given an array of filter group names for filter_group operations
            return true if this model matches all filter_groups.
            Not related to portal_groups.
            Filter groups are defined by adding a _filter_groups object to
            a model; key is group name, a boolean function does the filtering.
        */
            const self = this
            return _.every( self._filter_groups, function( fn, name ) {
                // Return true if filter name isn't in group or test passes
                return _.includes( filter_groups, name ) ? fn.apply( self ) : true
                })
            },
        // Named groups the model collections will know how to filter
        _filter_groups: {},

        /*-------------------------------------------------
            Other
        */

        natural_sort: function() {
        /*
            String for default ViewModel collectionObservables sorting.
            Override to add other default sorting
        */
            return ( this.get('tag') ? this.get('tag') : 'zzz' ) + this.get('name')
            },
        _set_natural_sort_hash: function( opts ) {
            // Set the natural sort attr using the natural sort method
            // This needs to be a string vs. a callable
            this.set( 'natural_sort', this.natural_sort(), opts )
            },

        logname: function() {
            return this.get('type_db') + "(" + this.id + ", " + this.cid + ")-" + this.get('name')
            },
        })

    })();
