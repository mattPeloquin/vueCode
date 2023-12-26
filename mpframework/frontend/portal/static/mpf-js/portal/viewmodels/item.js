/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Item Viewmodel
    Provides the base viewmodel behavior for most content
*/
(function() { 'use strict';

    mpp.ItemVM = function ItemVM( model ) {
        const self = Object.create( mpp.ItemVM.prototype )
        mpp.ItemVM.init( self, model )
        // Test for item vs. tree, group, type, category
        self.item_content = true
        return self
        }
    mpp.ItemVM.init = function( self, model ) {
        mpp.VmContent.init( self, model )

        self.tag = self.model.get('tag')
        self.slug = self.model.get('slug')

        // Observables for whether item is current
        self.is_current = ko.pureComputed( function() {
            return mpp.vm_current.item().id == self.id
            })

        // Override CSS classes to observe status
        const base_css_classes = self.css_classes
        self.css_classes = ko.pureComputed( function() {
            let rv = base_css_classes()
            rv += self.sb('image1') ? ' es_item_image' : ' es_item_textonly'
            // Add observables
            rv += ' ' + _state[ self.state() ][ CSS ]
            rv += self.is_current() ? ' es_current' : ''
            return rv
            })
        self.css_searchable = ko.pureComputed( function() {
            let rv = self.css_classes()
            rv += self.search_hidden() ? ' es_search_hidden' : ''
            return rv
            })

        // Observables for item state in the UI
        self.add_observable('status')
        self.state = ko.pureComputed( function() {
            const state = self.sb('access') ? self.sb('status') : 'locked'
            return ko.unwrap( state ) || 'default'
            })
        self.state_icon = ko.pureComputed( function() {
            return _state[ self.state() ][ ICON ]
            })
        self.state_text = ko.pureComputed( function() {
            return self.sbt('vm_item_status')[ self.state() ]
            })
        }
    mpp.ItemVM.prototype = _.extend( {}, mpp.VmContent.prototype, {

        /*
            Items normally render themselves and not nav templates,
            but support options for special cases.
        */
        render_nav: function( element ) {
            return this.sb_option( 'portal.render_nav', element )
            },
        render_item: function( element ) {
            return !this.sb_option( 'portal.render_no_item', element )
            },

        portal_groups: function() {
        /*
            Lazy check of what portal groups this content item/tree matches,
            returns list of all matching group VMs.
        */
            if( this._portal_groups === undefined ) {
                this._portal_groups = []
                // Add any groups whose tags match
                _.each( mpp.vm_groups, function( group ) {
                    if( group.in_group( this ) ) {
                        this._portal_groups.push( group )
                        }
                    })
                }
            return this._portal_groups
            },

        _css_classes: function() {
        /*
            Extend CSS types for items
        */
            let rv = mpp.VmContent.prototype._css_classes.call( this )
            if( this.action && this.action() ) {
                rv += ' es_action_' + this.action()
                }
            if( this.model.sb_option('portal.coming_soon') ) {
                rv += ' es_coming_soon'
                }
            return rv
            },

        search_hidden: function() {
        /*
            Returns true if global search observable is set and does not match.
            Don't hide the current item to avoid UI awkwardness.
        */
            let rv = false
            const search_value = mpp.search_value()
            if( search_value && !this.is_current() ) {
                rv = !this.search( search_value )
                }
            return rv
            },

        search: function( search_value ) {
        /*
            Return true of the given search value matches item.
            FUTURE - wildcard support
        */
            if( !this._search ) {
                // Cache blob for search values
                // Note the sb() checks will get parent values if blank
                this._search = [ this.id, this.name.toLowerCase(),
                    this.sb('search_tags').toLowerCase(),
                    this.sb('tag').toLowerCase(),
                    this.slug.toLowerCase(),
                    ].join(' ')
                }
            search_value = search_value.toLowerCase()
            return this._search.indexOf( search_value ) != -1
            },

        /*-------------------------------------------------
            Request access to content

            All requests to access content flow through here.
            If the request is made with a launcher, it will be called if getting
            access url was successful. If request is not successful or no launcher,
            the access dialog is shown.
        */
        request_access: function( launcher, node_id, direct_access ) {
            if( _access_active ) {
                mp.log_info("Ignoring access request due to active: " , this)
                return
                }
            _access_active = true
            mp.log_debug("Request access: ",this,", launcher: ",
                         launcher.name,", node: ",node_id," direct: ",direct_access)
            const self = this
            node_id = mp.safe_int( node_id )

            return mp.fetch({
                url: mpurl.api_item_access,
                method: 'POST',
                wait_indicator: true,
                json_data: {
                    'id': self.id,
                    'tree_id': node_id,
                    'direct_access': direct_access ? true : false,
                    },
                finished: function( access_data ) {
                    self.hide_wait()
                    try {
                        const access = mp.unpack_nested_json( access_data )
                        mp.log_info2("Request access returned with: ", access)

                        // Problem with configuration or session timeout
                        // Try reloading in case problem is with session/network; if a real
                        // config problem they should see message in access dialog
                        if( !access ) {
                            mpurl.reload_home()
                            }
                        // Server says user can access
                        else if( access.can_access ) {
                            // FUTURE -- more than one APA, implement APA selection for request
                            let success = false
                            if( access.access_url || access.direct ) {
                                // Progress was set to accessed on; set status based on the
                                // content semantics and update server
                                self.model.user_started()
                                // Add any progress data from user to item
                                self.model.set( 'progress_data', access.progress_data )
                                // Add item to the access data for use in viewer
                                access.item = self.model
                                // Execute the content access
                                success = launcher( access )
                                }
                            if( !success ) {
                                mp.dialog_open("This content is not yet available")
                                }
                            }
                        // Otherwise prompt to try/buy (make sure this item is visible)
                        else {
                            mpp.nav_set_path_content( node_id )
                            mp.access_dialog( access.pas, access.accounts )
                            }
                        }
                    catch( e ) {
                        mp.log_info("Error handling access request: ", e)
                        }
                    _access_active = false
                    }
                })
            },

        user_access: function( item, event ) {
        /*
            Event handler for access to VM's protected content.
            Except for direct URL, first entry point for user content access.
            The type of action is defined by the content (view, download, etc.)
        */
            mp.log_info2("User access requested:", item, event)
            event.stopPropagation()
            // Get selection from within DOM tree node the item was clicked on
            // Even though most UIs will already have this tree set as the current,
            // some UIs can show multiple trees on one screen
            const tree_element = $( event.target ).parents(".mp_tree_node")[0]
            const tree_id = tree_element && tree_element.getAttribute('data-content_id')
            const node = tree_id && mpp.vm_trees().get_id( tree_id )
            item.user_access_action( node )
            },

        user_access_action: function( node ) {
        /*
            Decide what happens when content items are accessed
            Returns True if request is going forward
        */
            // Skip if no content action or coming soon set
            if( !this.model.get('action') || this.model.sb_option('portal.coming_soon') ) {
                return
                }
            // Support use of current node, setting current node, and cases
            // where no current node is present (e.g., items outside tree UI)
            node && mpp.vm_current.node_set( node )
            node = mpp.vm_current.node()

            // Mark this VM as the current item
            mpp.vm_current.item_set( this )
            // Note any change in old item state
            const prev_model = mpp.vm_current.prev_item.model
            prev_model.update && prev_model.update()

            // Viewer options require navigation to show the viewer
            const action = this.model.get('action')
            if( _.startsWith( action, 'action_viewer' ) ) {
                mpp.start_content_viewer( this, node )
                }
            // For no content action, delegate to model
            else if( _.startsWith( action, 'action_none' ) ) {
                this.model.content_action()
                }
            // Other options open new tab and set location to url
            else {
                this.request_access( _get_tab_launcher( action ), node.id )
                }
            return true
            },

        action: function() {
            // User-friendly description of access action
            // This doesn't change so isn't an observable
            let rv = ''
            const action = this.model.get('action')
            if( _.startsWith( action, 'action_viewer' ) ) {
                rv = 'viewer'
                }
            else if( _.startsWith( action, 'action_inline' ) ) {
                rv = 'inline'
                }
            else if( _.startsWith( action, 'action_win' ) ) {
                rv = 'window'
                }
            return rv
            },
        action_icon: function() {
            // Return css class for action icon
            return _action[ this.model.get('action') ]
            },
        action_text: function() {
            // Return css class for action icon
            return this.sbt('vm_item_action')[ this.model.get('action') ]
            },

        })

    /*
        Only one request is allowed at a time since only one viewer is supported
        and scenarios where server isn't returning won't be helped by making
        extra requests.
    */
    let _access_active = false

    function _get_tab_launcher( action ) {
        let target = window
        if( _.startsWith( action, 'action_win' ) ) {
            // Open tab before ajax to avoid popup block
            target = window.open('about:blank')
            }
        else {
            // Otherwise downloading inline
            mp.inline_download = true
            }
        function launcher( access ) {
            if( access.item.id == mpp.vm_current.item().id ) {
                target.location = access.access_url
                return true
                }
            }
        return launcher
        }

    // CSS class lookup tables
    // FUTURE -- support override of VM css classes from sitebuilder data?
    const CSS = 0
    const ICON = 1
    const _state = {
        'no_state': [ '', '' ],
        'A':        [ 'es_state_accessed', 'fa fa-circle' ],
        'S':        [ 'es_state_started', 'fa fa-adjust fa-rotate-90' ],
        'C':        [ 'es_state_completed', 'fa fa-check-circle' ],
        'locked':   [ 'es_state_locked', 'fa fa-lock' ],
        'default':  [ 'es_state_available', 'fa fa-unlock-alt' ],
        }
    const _action = {
        'action_none':      '',
        'action_viewer':    'fa fa-play-circle',
        'action_win':       'fa fa-window-maximize',
        'action_inline':    'fa fa-download',
        'action_download':  'fa fa-download',
        }

    })();
