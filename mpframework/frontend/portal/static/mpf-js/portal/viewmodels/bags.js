/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Viewmodel bags and facades
    Singletons facades for accessing content viewmodels.
    Bags provide containers for holding one instance of each VM.
    Facades provide consistent aggregation APIs for accessing VMs in
    KO template code.
*/
(function() { 'use strict';

    /*
        Raw content Viewmodel bags
        These store one instance of each viewmodel that are accessed
    */
    mpp.vm_items = function() {
        return mpp.viewmodel_bag( 'items', mpp.ItemVM )
        }
    mpp.vm_trees = function() {
        return mpp.viewmodel_bag( 'trees', mpp.TreeVM )
        }
    mpp.vm_types = function() {
        return mpp.viewmodel_bag( 'types', mpp.TypeVM )
        }
    mpp.vm_groups = function() {
        return mpp.viewmodel_bag( 'groups', mpp.GroupVM )
        }
    mpp.vm_categories = function() {
        return mpp.viewmodel_bag( 'categories', mpp.CategoryVM )
        }

    /*
        Main viewmodel content facade bag
        CONTEXT FOR MAIN PAGE KO BINDING, includes key default content
        groupings and other convenience accessors.
    */
    const _MainVMs = function() {
        let self = Object.create( _MainVMs.prototype )
        // Hide/show of navigation items - managed in set_path
        self.show_breadcrumbs = ko.observable()
        return self
        }
    _MainVMs.prototype = _.extend( {}, mpp.VmShared.prototype, {

        // Default context groups used in templates
        all_items: function() {
            return mpp.vm_items().all_sorted()
            },
        all_tops: function() {
            return mpp.vm_trees().all_tops()
            },
        all_nodes: function() {
            return mpp.vm_trees().all_nodes()
            },
        all_content: function() {
            return _.concat( mpp.vm_main.all_tops(), mpp.vm_main.all_items() )
            },
        // Grouping values
        // FUTURE Finish scope filter
        types: function( scope ) {
            return mpp.vm_types().all_sorted()
            },
        groups: function( scope ) {
            return mpp.vm_groups().all_sorted()
            },
        categories: function( scope ) {
            return mpp.vm_categories().all_sorted()
            },

        get_tag: function( tag ) {
            return mpp.vm_trees().get_tag( tag ) || mpp.vm_items().get_tag( tag )
            },

        logname: function() { return 'VM-content' },
        })

    mpp.vm_main = _MainVMs()

    })();
