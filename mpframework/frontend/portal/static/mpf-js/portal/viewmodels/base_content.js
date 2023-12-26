/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Base ViewModel for all content
*/
(function() { 'use strict';

    mpp.search_value = ko.observable()

    mpp.VmContent = function( model ) {
        const self = Object.create( mpp.VmContent.prototype )
        mpp.VmContent.init( self, model )
        return self
        }

    mpp.VmContent.init = function( self, model ) {
    /*
        Content VM constructor
        Make sure underlying model is fully initialized and add data held by
        each ViewModel instance. Many model attributes don't change so
        are not observables and are left in the model.
        Observables which are always called by the UI should be created
        in the init constructor, whereas items that may not be used
        can be lazily instantiated in prototype factory methods.
    */
        model.lazy_init()
        _.extend( self, Backbone.Events, {

            // Convenience model items
            model: model,
            type_db: model.get('type_db'),
            type_name: model.get('type_name'),

            // Cache any observables and mappings to manage with get()
            _observables: {},
            _mappings: false,

            // Setup local variables for frequently accessed items
            // that may be duck-typed in shared code AND which
            // do not need observables
            id: self.VM_ID_PREFIX + model.id,
            name: model.get('name'),

            // Identify items from other content
            item_content: false,

            // Observable for updating css class string
            // Items that don't change are added in _css_classes
            css_classes: ko.pureComputed( function() {
                if( !self._classes ) {
                    self._classes = self._css_classes()
                    }
                return self._classes
                }),
            _classes: '',

            })
        //mp.log_debug("CREATING", self.logname())
        }

    mpp.VmContent.prototype = _.extend( {}, mpp.VmShared.prototype, {

        jQuery: function( scope ) {
            scope = scope || document.body
            return $( scope ).find( '.es_id_' + this.id )
            },

        sb: function( attr, element ) {
        /*
            Return SiteBuilder value or observable.
            Descriptive way to access model content from templates
            The sb name is intended to be easy to read in templates.

            Some attributes will check their vm parents (in HTML structure)
            for values if not present.
        */
            // Apply any optional mappings to change one attr to another
            if( this._mappings === false ) {
                this._mappings = mpp.sb_option( 'portal.attr_mappings', '', this )
                }
            if( this._mappings ) {
                const mapping = this._mappings[ attr ]
                if( mapping && this.model.get( mapping ) ) {
                    attr = mapping
                    }
                }

            // Return observable if one exists or should be created
            let observable = this._observables[ attr ]
            if( !observable ) {
                if( this.model.more_to_load( attr ) ) {
                    // If dynamic, create new observable and start load
                    observable = this.add_observable( attr )
                    if( !this.model.fully_loaded ) {
                        this.model.load_full()
                        }
                    }
                }
            if( observable !== undefined ) {
                return observable
                }

            // Check item and potentially parents
            let rv = this.model.get( attr )
            if( rv !== undefined ) {
                if( !rv && element ) {
                    const context = ko.contextFor( element )
                    if( context && context.$parents ) {
                        context.$parents.some( function( parent ) {
                            rv = parent.sb && parent.sb( attr )
                            return !!rv
                            })
                        }
                    }
                return rv
                }

            mp.log_debug_level && mp.log_debug("Missing sb('" + attr + "'): ",
                    this.logname())
            return ''
            },

        get_model_id: function( vm_id ) {
        /*
            Given a VM ID, return the model ID for this type
            Allows creating different VM namespaces beyond the
            default shared Item/Tree integer ID namespace by
            overriding VM_ID_PREFIX
        */
            let id = vm_id || this.id
            if( this.VM_ID_PREFIX && !_.toInteger( id ) ) {
                id = _.trimStart( id, this.VM_ID_PREFIX )
                return _.toInteger( id )
                }
            else {
                return _.toInteger( id )
                }
            },
        VM_ID_PREFIX: '',

        add_observable: function( attr, change_fn ) {
        /*
            Create KO observable for backbone attribute
        */
            const observable = ko.observable( this.model.get( attr ) )
            this._observables[ attr ] = observable

            // Link the ViewModel observable to changes in model attribute
            this.listenTo( this.model, 'change:' + attr,
                function( model, options ) {
                    //mp.log_debug("CHANGE ->", attr + ":", model.logname())
                    observable( model.get( attr ) )
                    })

            // Optional subscription function for change events
            change_fn && observable.subscribe( change_fn )

            return observable
            },

        /*
            Default templates for rendering a bag of content in items.html
        */
        render_nav: function() {
            return true
            },
        render_item: function() {
            return false
            },

        show_wait: function( msg ) {
            this.jQuery().show_wait( msg )
            },
        hide_wait: function( msg ) {
            this.jQuery().hide_wait()
            },

        _css_classes: function() {
        /*
            Create string with content css classes
            Return value is an object for the KO class binding, so observables
            in the object will be managed by KO.
            Specializations can add tags as needed
        */
            let rv = `es_id_${ this.id } es_content_${ this.type_name.toLowerCase() }`
            if( this.tag ) {
                rv += ` es_license_${ this.tag }`
                }
            if( this.slug ) {
                rv += ` es_slug_${ this.slug }`
                }
            if( this.model.get('workflow') != 'P' ) {
                rv += ` es_workflow_${ this.workflow() }`
                }
            if( this.model.get('portal_type') ) {
                rv += ' es_type_' + _.replace(
                        this.model.get('portal_type'), /\s/g, '-' )
                }
            if( this.model.get('portal_group') ) {
                rv += ' es_group_' + _.replace(
                        this.model.get('portal_group'), /\s/g, '-' )
                }
            // Get additional css classes from SiteBuilder options
            const classes = this.sb_option('portal.css_classes')
            if( classes ) {
                rv += ' ' + classes
                }
            return rv
            },

        workflow: function() {
            // User-friendly workflow desc; doesn't change so not observable
            return _workflow[ this.model.get('workflow') ] || "retired"
            },

        dialog: function( attr ) {
            // If attribute exists, show it in a dialog
            const value = ko.unwrap( this.sb( attr ) )
            value && mp.dialog_open( value )
            },

        logname: function() {
            return "VM-" + this.type_db + this.id + ': ' + this.name
            },
        })

    // User friendly lookups
    const _workflow = {
        'D': "dev",
        'B': "beta",
        'P': "prod",
        }

    })();
