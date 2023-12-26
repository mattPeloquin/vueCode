/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Content ViewModel base bag support
*/
(function() { 'use strict';

    /*--------------------------------------------------------------
        Create and cache viewmodels and bags of viewmodels

        There is one VM for every model instance. These are cached and
        hold UI state shared across all HTML presentations of that item.

        VM bags are groupings of item VMs that may be displayed 0:n times
        in the UI with different filtering and sorting.

        Only specific attributes of items or bags that may change within
        a user session are made KO observables.
    */

    mpp.viewmodel_bag = function( models_name, viewmodel ) {
        const key = models_name + viewmodel.name
        if( !_viewmodel_bags[ key ] ) {
            // Cache the view models for the given bag and type
            _viewmodel_bags[ key ] = viewmodel.VmBag ?
                    viewmodel.VmBag( mpp.models[ models_name ] ) :
                    mpp.VmBag( mpp.models[ models_name ], viewmodel )
            }
        return _viewmodel_bags[ key ]
        }
    let _viewmodel_bags = {}

    function _get_or_create_viewmodel( model, vm_class ) {
        // Return cached VM for the model object
        if( !_viewmodels[ model.cid ] ) {
            _viewmodels[ model.cid ] = _viewmodel( model, vm_class )
            }
        return _viewmodels[ model.cid ]
        }
    let _viewmodels = {}

    function _viewmodel( model, vm_class_default ) {
    /*
        Viewmodel Polymorphism based on model
        Try to get a specialized viewmodel based on model type
        If none exists, use the default
    */
        // HACK - convention for ViewModel class name based on model type
        const vm_class_name = _.capitalize( model.get('type_db') ) + "VM"
        const vm_class = mpp[ vm_class_name ] || ( vm_class_default || mpp.ItemVM )
        return vm_class( model )
        }

    /*--------------------------------------------------------------
        ViewModel Bag base

        VM bags are responsible for creating and sharing VM objects
        and providing filtered and sorted subsets. Thry hold a
        reference to a Backbone model collection and lazily create
        and cache viewmodels for those models.

        Bags are used in the UI for collections, and manage collection
        node content, but do not represent Tree/Collection metadata.

        viewmodels() factory is used to create accessors that return
        filtered arrays or observableArrays of VMs depending on whether
        the filtered set can change during a portal session.
    */
    mpp.VmBag = function( models, viewmodel ) {
        const self = Object.create( mpp.VmBag.prototype )
        self.viewmodel = viewmodel
        mpp.VmBag.init( self, models )
        return self
        }
    mpp.VmBag.init = function( self, models ) {
        self._models = models

        // Get all vms in this bag
        self.accessor( 'all_sorted', function() {
            return self.viewmodels({ sort: true })
            })

        // The bag's retrieval state
        self.fetched = ko.observable( self._models, 'fetched' )
        self.empty = ko.pureComputed( function() {
            return self.fetched() && !self._models.length
            })
        }
    mpp.VmBag.prototype = _.extend( {}, mpp.VmShared.prototype, {

        get_name: function( name ) {
        /*
            Get one item by script_name or name
        */
            return this.vm_attr({ 'script_name': [ name ] })[0] ||
                    this.vm_attr({ 'name': [ name ] })[0]
            },

        viewmodels: function( options ) {
        /*
            Factory for routines to return filtered arrays of viewmodels,
            with caching and KO observable chain support.
            Returns new filtered and sorted array of VM references
            Creates and caches ViewModel if it doesn't exist
            If the bag could be updated dynamically, the returned
            array should be converted into a KO observableArray
        */
            let rv = []
            // Default options
            options = _.extend( {
                viewmodel: this.viewmodel,
                // Default to server ordering
                sort: false,
                sort_attr: 'natural_sort',
                }, options || {} )
            // Iterate through filtered models creating/getting VM for result set
            this.models( options ).forEach( function( model ) {
                rv.push( _get_or_create_viewmodel( model,
                            options && options.viewmodel ) )
                })
            // If sort defined in options
            if( options.sort && options.sort_attr ) {
                rv = _.sortBy( rv, function(vm) {
                        return vm.model.get( options.sort_attr )
                        })
                if( options.sort == 'desc' ) {
                    rv.reverse()
                    }
                }
            return rv
            },

        models: function( options ) {
        /*
            Return filtered array of models
            Used to create subsets of both model and viewmodel bags
        */
            let rv = []
            options = options || {}

            // If optimized model filter provided, cut list down to that first
            let models = this._models
            if( options.tops && this._models.roots ) {
                models = models.roots()
                }
            if( options.ids ) {
                models = models.id_filter( options.ids )
                }
            if( options.where ) {
                models = models.where( options.where )
                }
            if( options.findWhere ) {
                const model = models.findWhere( options.findWhere )
                models = model ? [ model ] : []
                }
            // Then loop through each model; make sure it is initialized
            // and perform filter operations
            models.forEach( function( model ) {
                model.lazy_init()
                if( _filter_groups( model, options ) &&
                        _filter_system( model ) ) {
                    if( !options.model_filter || options.model_filter( model ) ) {
                        rv.push( model )
                        }
                    }
                })
            return rv
            },

        _filter_attr: function( filters, options, items ) {
        /*
            Filter model attr factory
            filters is a dict of attr names with valid values lists:

                { status: ['C'], access: [true] }

            items is an array of models or viewmodels to be filtered.
            Returns observable of items that pass all filters.

            FUTURE - could use options to adjust filter from _.includes criteria
        */
            options = options || {}
            const orig_model_filter = options.model_filter
            options = _.extend( options, {
                model_filter: function( item ) {
                    return _.every( _.toPairs( filters ), function( pair ) {
                        // Check for array or substring match with attribute value
                        const value = item.get( pair[0] )
                        const check = pair[1]
                        if( _.isArray( check ) ? _.includes( check, value ) :
                                _.includes( value, check ) ) {
                            // Chain call to existing model_filter if needed
                            return orig_model_filter ?
                                    orig_model_filter( item ) : true
                            }
                        })
                    },
                })
            return items.call( this, options )
            },
        models_attr: function( filters, options ) {
            return this._filter_attr( filters, options, this.models )
            },
        vm_attr: function( filters, options ) {
            return this._filter_attr( filters, options, this.viewmodels )
            },

        logname: function() {
            return "VMbag-" + this.viewmodel.name
            },
        })

    function _filter_groups( model, options ) {
    /*
        Filter by configured model filter_groups
    */
        if( !options.filter_groups ) {
            return true
            }
        return model.in_filter_groups( options.filter_groups )
        }

    function _filter_system( model ) {
    /*
        Returns false if model shouldn't be displayed based on
        system parameters and content configuration, such
        that a VM won't be created.
        This includes checking workflow against user state,
        hiding due to access and managing the prod-retire setting.

        Check as part of model groups being created by VMs so only
        the VM groups that need to be displayed are processed.
        This only checks global options to optimize VM creation;
        some options may also be checked on display.
    */
        // Don't display retired items, which should only be present
        // when timewin delta is overriding
        if( model.get('workflow') === 'R' ) {
            return false
            }
        // Dev workflow sees everything else that is sent over
        if( _.includes( mp.user.workflow, 'D' ) ) {
            return true
            }
        // Reject if no access and hide if no access is on
        if( mpp.sb_option('portal.hide_if_no_access') ||
                model.sb_option('portal.hide_if_no_access') ) {
            if( !mpp.access_item( model ) ) {
                return false
                }
            }
        // Check any user level restrictions
        const user_level = mpp.sb_option('portal.user_level') ||
                model.sb_option('portal.user_level')
        if( !mpp.check_user_level( user_level ) ) {
            return false
            }
        // If item is prod-retired, show if started and not currently a trial
        if( model.get('workflow') === 'Q' ) {
            return !!( model.get('status') && !model.sb_option('portal.no_trials') )
            }
        // Check trees for any items that are started
        if( is_prod_retire_root_item( model.id ) ) {
            return true
            }
        // Otherwise whether to show item/node is based on workflow
        return _.includes( mp.user.workflow, model.get('workflow') )
        }

    function is_prod_retire_root_item( item_id ) {
        // If a user has started a top-level collection that is prod-retire,
        // all content in that collection is shown.
        if( !_prod_retire_active_root_items.length ) {
            mpp.models.trees.each( function( tree ) {
                // Since called from model filter, cannot use VM or Model filters here
                if( tree.is_root() && tree.get('workflow') === 'Q' &&
                        tree.get('status') && !tree.sb_option('portal.no_trials') ) {
                    _prod_retire_active_root_items = [].concat(
                            _prod_retire_active_root_items,
                            tree.get('all_nodes'), tree.get('all_items') )
                    }
                })
            }
        return _.includes( _prod_retire_active_root_items, item_id )
        }
    // Cache of items covered by prod-retired item that is active
    let _prod_retire_active_root_items = []

    })();
