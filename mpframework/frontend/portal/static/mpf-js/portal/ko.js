/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Knockout bindings, config, and extensions

    For most bindings MPF passes VM explicity as value for
    the binding and then unwraps. This makes it clearer
    in the template code what the VM is, and allows some
    flexibility for some binding situations.
*/
(function() { 'use strict';

    const CLEAN_DELAY = 1000

    // Return length of either array or observableArray
    ko.length = function( collection ) {
        return collection && ko.unwrap( collection ).length
        }

    // Change default compare to include objects
    ko.observable.fn['equalityComparer'] = function( a, b ) {
        return a == b
        }

    // Defer updates to avoid unnecessary updating
    ko.options.deferUpdates = true

    // Override KO behavior to log exceptions in async handlers
    // AND not throw uncaught exception
    ko.utils.deferError = function( error ) {
        setTimeout( function() {
            ko.onError( error )
            }, 0)
        }
    ko.onError = function( error ) {
        mp.log_error("Knockout error: ", error)
        }

    /*
        KO bindings
        A basic portal can run off of one binding to a VM bag, while
        more complex portals use modular UIs that are lazily created.
    */

    mpp.ko_apply_bindings = function() {
    /*
        Apply KO bindings to HTML via classes
    */
        mp.log_time_start("KO Viewmodel binding")
        _.over( mpp.ko_bindings )()
        mp.log_time_mark("KO Viewmodel binding")
        }
    mpp.ko_bindings = [
        function() { mpp.ko_binding_apply( 'main_page', mpp.vm_main ) },
        ]

    mpp.ko_binding_apply = function( selector, vm ) {
    /*
        All KO bindings run through here.
        Each time this is called, a NEW $root KO binding context is created.
    */
        $( selector ).each( function bind_element( _, node ) {
            try {
                // Highlight issue with binding KO items under lazy nodes
                if( node.nodeType === 8 && node.nodeValue.match(/ko if/) ) {
                    mp.log_error("ERROR cannot start binding on KO logic node",
                                _display(node), " -> ", vm.logname() )
                    }
                // Do the binding with valid DOM node
                if( node.nodeType === 1 || node.nodeValue.match(/ko template/) ) {
                    mp.log_debug("binding: ", vm.logname(), " -> ", _display(node))
                    setup_binding_clean( node )
                    ko.applyBindings( vm, node )
                    mp.log_info2("BOUND: ", vm.logname(), " -> ", _display(node))
                    }
            } catch( e ) {
                mp.log_error("BINDING EXCEPTION ", _display(node), " -> ",
                                (vm && vm.logname) ? vm.logname() : vm, "\n", e)
                mp.debugger()
                }
            })
        function _display( node ) {
            return node[ node.nodeType === 1 ? 'className' : 'nodeValue' ]
            }
        }

    // Support easy extension of some bindings
    ko.bind_extend = {
        bind_nav_content: { init: [] }
        }
    function run_bind_extensions( name, handler, element, value ) {
        _.each( ko.bind_extend[ name ][ handler ],
            function( extension ) {
                extension( element, value )
                })
        }

    /*
        Lazy binding for content display.
        Delay creation of VMs and DOM elements (and loading their resources),
        which is good for performance and CRITICAL for scaling KO.

        NOTE - Non-nav lazy binding relies on Observers, so be careful how
        they are applied (since there can be 1000s of content items).

        NOTE - CANNOT USE KO COMMENT IF BINDINGS AS CHILD OF A LAZY BIND NODE
        KO doesn't reliably directly bind these nodes, generating
        "Found end comment without a matching opening comment" errors.
        The lazy binding node is already bound, so it binds all children,
        so the template HTML needs to ensure only DOM nodes or KO templates.
    */

    ko.bindingHandlers.lazy_bind_pane = {
        // Bind pane panel when navigated to
        init: function( element, value, _ab, _vm, context ) {
            const vm = lazy_init( element, value )
            mp.log_debug("Lazy pane bind: ", element, vm)
            nav_panel_init( element, vm, context )
            // Register handler to bind nested nav structures when shown
            mp.nav_initial_handlers[ element.id ] = function() {
                    lazy_vm_bind( element, vm, context )
                    }
            return { controlsDescendantBindings: true }
            }
        }

    ko.bindingHandlers.lazy_bind_top_panel = {
        // Bind top-level collection panel when navigated to
        init: function( element, value, _ab, _vm, context ) {
            const vm = lazy_init( element, value )
            mp.log_debug("Lazy top panel bind: ", element, vm)
            nav_panel_init( element, vm, context )
            mpp.set_background( element, vm )
            add_style( element, vm, 'portal.collection_styles' )
            // Register handler to bind nested nav structures when shown
            mp.nav_initial_handlers[ element.id ] = function() {
                    lazy_vm_bind( element, vm, context )
                    }
            return { controlsDescendantBindings: true }
            }
        }

    ko.bindingHandlers.lazy_bind_mphidden = {
        // Binding when mp_hidden class removed
        init: function( element, value, _ab, _vm, context ) {
            const vm = lazy_init( element, value )
            mp.log_debug("Lazy hidden bind: ", element, vm)
            lazy_class_remove( element, 'mp_hidden', function( target ) {
                    lazy_vm_bind( target, vm, context )
                    })
            return { controlsDescendantBindings: true }
            }
        }

    ko.bindingHandlers.lazy_bind_visible = {
        // Bind based on intersection visibility
        init: function( element, value, _ab, _vm, context ) {
            const vm = lazy_init( element, value )
            mp.log_debug("Lazy visible bind: ", element, vm)
            const observer = new IntersectionObserver(
                function bind_visible( entries ) {
                    entries.forEach( function( entry ) {
                        if( entry.intersectionRatio > 0 ) {
                            lazy_vm_bind( element, vm, context )
                            observer.disconnect()
                            }
                        })
                })
            observer.observe( element )
            return { controlsDescendantBindings: true }
            }
        }

    // Force select of item (either initial display or after lazy loading)
    ko.bindingHandlers.bind_nav_show = {
        init: function( element, value, _all, bc ) {
            // If true passed, select this item
            let show = ( ko.unwrap( value() ) === true )
            // Otherwise select if first from a foreach binding #}
            if( !show ) {
                show = !!( bc.$index && bc.$index() == 0 )
                }
            if( show ) {
                $( element ).removeClass('mp_nav_hide')
                }
            }
        }

    /*
        Non-lazy bindings support nesting panels and nav cards/anchors
    */

    ko.bindingHandlers.bind_nav_panel = {
        // Setup content nav panels (tree children, home page, other content)
        init: function( element, value, _ab, _vm, context ) {
            const vm = value && ko.unwrap( value() )
            mp.log_debug("Nav panel bind: ", element, vm)
            nav_panel_init( element, vm, context )
            if( !vm ) {
                mpp.set_background( element )
                }
            },
        update: function( element ) {
            filter_results( element )
            }
        }
    ko.bindingHandlers.bind_nav_panel_nest = {
        // Setup content nav panels (tree roots or otherwise)
        init: function( element, value, _ab, _vm, context ) {
            const vm = value && ko.unwrap( value() )
            mp.log_debug("Nav nested bind: ", element, vm)
            init_nav( element, vm, true )
            content_panel_init( element, vm, context )
            },
        update: function( element ) {
            filter_results( element )
            }
        }

    // Create nav element for top-level and nested content panels
    ko.bindingHandlers.bind_nav_content = {
        init: function( element, value ) {
            _nav_content( element, value )
            },
        }
    ko.bindingHandlers.bind_nav_content_nest = {
        init: function( element, value ) {
            _nav_content( element, value, true )
            },
        }
    function _nav_content( element, value, nested ) {
        const vm = ko.unwrap( value() )
        ko.bindingEvent.subscribe( element, 'childrenComplete',
            function nav_ready() {
                nav_link_init( element, vm, !nested )
                item_init( element, vm )
                add_style( element, vm, 'portal.nav_styles' )
                !nested && run_bind_extensions( 'bind_nav_content', 'init', element )
                })
        }

    // For non-content nav links
    ko.bindingHandlers.bind_nav_link = {
        // Use with elements at same URL level as parent
        init: function( element, value ) {
            const vm = ko.unwrap( value() )
            ko.bindingEvent.subscribe( element, 'childrenComplete',
                function nav_ready() {
                    nav_link_init( element, vm, true )
                    })
            },
        }
    ko.bindingHandlers.bind_nav_link_nest = {
        // Set nav link to point to panel and set reference id
        init: function( element, value ) {
            const vm = ko.unwrap( value() )
            nav_link_init( element, vm )
            },
        }

    /*
        Other bindings for content setup and dynamic styling
    */

    ko.bindingHandlers.bind_content_panel = {
        // Bind top of content display panel (usually a root)
        init: function( element, value, _ab, _vm, context ) {
            const vm = value && ko.unwrap( value() )
            mp.log_debug("Content panel bind: ", element, vm)
            content_panel_init( element, vm, context )
            },
        update: function( element ) {
            filter_results( element )
            }
        }

    ko.bindingHandlers.bind_tree_node = {
        // Bind top and nested tree nodes
        init: function( element, value, _ab, _vm, c ) {
            const tree = ko.unwrap( value() )
            mp.log_debug("Tree node bind: ", element, tree)
            tree.mpp_context = c
            element.setAttribute( 'data-content_id', tree.id )
            add_style( element, tree, 'portal.collection_styles' )
            ko.bindingEvent.subscribe( element, 'childrenComplete',
                function tree_ready() {
                    tree_node_viz( element )
                    list_init( element )
                    })
            },
        update: function( element ) {
            filter_results( element, true )
            }
        }

    ko.bindingHandlers.bind_items = {
        // Bind items outside a tree node
        init: function( element ) {
            mpp.css_toggle_init( element )
            },
        update: function( element ) {
            filter_results( element )
            }
        }

    ko.bindingHandlers.bind_item = {
        // Bind individual content items
        init: function( element, value ) {
            const item = ko.unwrap( value() )
            mp.log_debug("item bind: ", element, item)
            ko.bindingEvent.subscribe( element, 'childrenComplete',
                function item_ready() {
                    mpp.change_on_hover( element )
                    item_init( element, item )
                    add_style( element, item, 'portal.item_styles' )
                    })
            }
        }

    ko.bindingHandlers.bind_display = {
        // Display of ko rendered content
        init: function( element ) {
            init_element( element )
            }
        }

    ko.bindingHandlers.bind_menu = {
        // Targeted initialize of menu after biding complete
        init: function( element ) {
            init_menu( element )
            }
        }

    ko.bindingHandlers.bind_hide_no_results = {
        // Display elements that should hide if no items in them after filter
        update: function( element ) {
            filter_results( element, true )
            }
        }

    ko.bindingHandlers.update_draggable = {
        update: function( element ) {
            mp.style_add_draggable( element )
            }
        }

    // Shared code for lazy binding

    function lazy_init( element, value ) {
        // Setup element for future lazy binding
        const vm = ko.unwrap( value() )
        element.setAttribute( 'data-lazy_bind', vm.name )
        return vm
        }

    function lazy_vm_bind( element, vm, context ) {
    /*
        Bind ELEMENT'S CHILDREN after it has passed lazy criteria.
        Adds any context from the lazy binding point to the viewmodel.
    */
        if( element.hasAttribute('data-lazy_bind') ) {
            element.removeAttribute('data-lazy_bind')
            vm.mpp_context = context
            mpp.ko_binding_apply( element.childNodes, vm )
            init_element( element )
            if( vm.lazy_fn ) {
                vm.lazy_fn( element )
                }
            }
        }

    // Shared code for nav panel and link bindings

    function init_nav( element, vm, nested ) {
        const path = mpp.nav_path( element, vm )
        mpp.nav_set_panel( element, path, nested, vm )
        }
    function nav_link_init( element, vm, ignore_parent ) {
        const path = mpp.nav_path( element, vm, ignore_parent )
        mp.nav_set_link( element, path )
        }

    function nav_panel_init( element, vm, context ) {
        // Shared code for initializing nav panels
        init_nav( element, vm )
        init_menu( element )
        content_panel_init( element, vm, context )
        }

    function init_menu( element ) {
        // Initialize nested menus after a binding
        ko.bindingEvent.subscribe( element, 'childrenComplete', function() {
            if( mp.user.access_staff ) {
                mp.init_menus( element, 'mp_menu_highlight' )
                }
            })
        }

    // Shared code for content bindings

    function content_panel_init( element, vm, context ) {
    /*
        Shared code for initializing panels that hold content.
        If the panel is a content collection/group vm will be valid.
    */
        if( vm && vm.id ) {
            vm.mpp_context = context
            element.setAttribute( 'data-content_id', vm.id )
            }
        // Update everything in panel once DOM creation is complete
        ko.bindingEvent.subscribe( element, 'childrenComplete',
            function panel_ready() { setTimeout( function() {
                init_element( element )
                }, 0)
            })
        }

    function init_element( element ) {
        mp.init_tooltips( element )
        mp.init_clipboard_buttons( element )
        mp.viz_add_toggle( element )
        mpp.init_controls( element )
        mpp.css_toggle_init( element )
        }

    function tree_node_viz( element ) {
        const tree = $( element )
        mp.viz_set_toggle(
                tree.find('.mp_viz_content_toggle').first(),
                tree.find('.mp_viz_content_body').first(),
                { no_icon: true })
        }

    function item_init( element, vm ) {
        const item = $( element )
        // Setup any hide/show viz
        mp.viz_set_toggle(
                item.find('.mp_viz_content_toggle'),
                item.find('.mp_viz_content_body'),
                { no_icon: true, no_pointer: true,
                    switch_toggle_class: 'es_theme_current',
                    viz_fn: vm.viz_fn,
                    })
        // Add card/list css from template theme to root item element
        // Done here because the card/list theme for the item parent element
        // isn't known until item's template is rendered
        item.filter(":has(.es_theme_list)")
            .addClass('es_content_list')
        item.filter(":has(.es_theme_card)")
            .addClass('es_content_card')
        item.filter(":has(.es_content_full)")
            .addClass('es_content_full')
        // Add tooltip to item if the template defined it
        item.filter( function() {
            return item.find("tooltip").length
            }).addClass('mp_tooltip')
        }

    function filter_results( element, hide_empty ) {
    /*
        Hide items based on search and category filters
    */
        // Wrap in set timeout to allow items under tree to be updated
        const search = mpp.search_value()
        setTimeout( function() {
            if( search ) {
                const items = $( element ).find('.es_content:not(.es_search_hidden)').length
                if( hide_empty ) {
                    $( element ).toggleClass( 'es_search_hidden', !items )
                } else {
                    $( element ).find('.mp_no_results').toggleClass('mp_hidden', !!items )
                    }
                }
            else {
                if( hide_empty ) {
                    $( element ).removeClass('es_search_hidden')
                } else {
                    $( element ).find('.mp_no_results').addClass('mp_hidden')
                    }
                }
            })
        }

    function list_init( element ) {
    /*
        Standardized list.js config that templates can use for ONE list,
        based on positional ordering of mp_list elements under es_content_body.
    */
        const list_rows = $( element ).find(".mp_list_row")
        if( list_rows.length ) {
            const list_columns = list_rows.first().children("[class*='mp_list']")
            if( list_columns.length ) {
                // Add column header placeholder
                const header = $('<div class="es_list_header mp_flex_line"></div>')
                        .prependTo( $( element ).find(".es_items") )
                // Determine how many columns
                const column_classes = []
                list_columns.each( function( index, column ) {
                    const column_name = 'mp_list' + ( index + 1 )
                    column_classes.push( column_name )
                    // Add header
                    const header_title = $( column ).data('column') || ''
                    $('<div class="mp_sort ' + column_name +
                            '" data-sort="' + column_name + '">' +
                        header_title +
                        '</div>')
                            .appendTo( header )
                    })
                // Setup the list
                $( element ).find(".es_items_container").addClass('mp_list')
                const list = new List( element, {
                        listClass: 'mp_list',
                        sortClass: 'mp_sort',
                        valueNames: column_classes,
                        })
                // Default to first column sort
                list.sort( 'mp_list1', { order: 'asc' } )
                }
            }
        }

    function lazy_class_remove( element, class_name, bind_fn ) {
    /*
        Lazy bind an element when the given class_name is removed
    */
        const observer = lazy_vm_binder( function( target ) {
                    return !target.classList.contains( class_name )
                    },
                bind_fn
                )
        observer.observe( element, {
            attributes: true,
            attributeFilter: ['class'],
            })
        return observer
        }
    function lazy_vm_binder( test_fn, bind_fn ) {
        // Return observer that executes bind_fn based on test_fn
        const observer = new MutationObserver(
            function( mutations ) {
                mutations.forEach( function( mutation ) {
                    if( test_fn( mutation.target ) ) {
                        bind_fn( mutation.target )
                        observer.disconnect()
                        }
                    })
            })
        return observer
        }

    function add_style( element, vm, style ) {
    /*
        Utility for adding style to bound element
    */
        const style_text = vm.sb_option( style, element )
        if( style_text ) {
            $( element ).attr( 'style', style_text )
            }
        }

    function setup_binding_clean( element ) {
    /*
        Inspecting DOM for CSS updates is important to web developers. KO markup
        can get messy, especially with extra lines from server scripting.
        Since most KO is used for initial rendering, it is safe to remove.
    */
        if( !mpp.keep_ko_bindings ) {
            ko.bindingEvent.subscribe( element, 'childrenComplete', _clean_bindings )
            }
        }
    function _clean_bindings( node ) {
        // No need to incur overhead in main render
        setTimeout( function() {
            // Current binding node is passed in; use parent if ko template comment
            node = $( node )
            if( _is_comment( null, node[0] ) ) {
                node = node.parent()
                }
            // Exclude lazy bindings under current render
            const lazy_roots = node.find("[data-lazy_bind]")
            const lazy = $( lazy_roots ).find("[data-bind]")
            const rendered = node.find("[data-bind]").addBack().not( lazy )
            // Remove the KO in the binding elements
            rendered.removeAttr('data-bind')
            // Remove any comment virtual nodes that are direct children
            //rendered.contents().filter( _is_comment ).remove()
            node.find("*").not( lazy_roots.find("*").addBack() )
                        .contents().filter( _is_comment ).remove()
            }, CLEAN_DELAY )
        }
    function _is_comment( _index, child ) {
        return child.nodeType === 8
        }

    })();
