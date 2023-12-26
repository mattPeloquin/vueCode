/*!
    MPF updates to Django MPTT Draggable admin

    PORTIONS ADAPTED FROM OPEN SOURCE:
      https://github.com/django-mptt/django-mptt
 */

mp.when_ui_loaded( function mptt_init() {

    /* PORTIONS ADAPTED FROM OPEN SOURCE:
         https://github.com/jquery/jquery-ui/blob/master/ui/disable-selection.js
    */
    jQuery.fn.extend({
        disableSelection: (function() {
            var eventType = 'onselectstart' in document.createElement('div') ? 'selectstart' : 'mousedown';

            return function() {
                return this.on(eventType + '.ui-disableSelection', function(event) {
                    event.preventDefault();
                });
            };
        })(),

        enableSelection: function() {
            return this.off('.ui-disableSelection');
        }
    });

    jQuery(function($){
        // We are not on a changelist it seems.
        if (!document.getElementById('result_list')) return;

        var DraggableMPTTAdmin = null;

        function isExpandedNode(id) {
            return DraggableMPTTAdmin.collapsedNodes.indexOf(id) == -1;
        }

        function markNodeAsExpanded(id) {
            // remove itemId from array of collapsed nodes
            var idx = DraggableMPTTAdmin.collapsedNodes.indexOf(id);
            if(idx >= 0)
                DraggableMPTTAdmin.collapsedNodes.splice(idx, 1);
        }

        function markNodeAsCollapsed(id) {
            if(isExpandedNode(id))
                DraggableMPTTAdmin.collapsedNodes.push(id);
        }

        function treeNode(pk) {
            return $('.tree-node[data-pk="' + pk + '"]');
        }

        // toggle children
        function doToggle(id, show) {
            var children = DraggableMPTTAdmin.treeStructure[id] || [];
            for (var i=0; i<children.length; ++i) {
                var childId = children[i];
                if(show) {
                    treeNode(childId).closest('tr').show();
                    // only reveal children if current node is not collapsed
                    if(isExpandedNode(childId)) {
                        doToggle(childId, show);
                    }
                } else {
                    treeNode(childId).closest('tr').hide();
                    // always recursively hide children
                    doToggle(childId, show);
                }
            }
        }

        function rowLevel($row) {
            try {
                return $row.find('.tree-node').data('level') || 0;
            } catch( e ) {
                return 0;
            }
        }

        /* Thanks, Django */
        function getCookie(name) {
            var cookieValue = null;
            if (document.cookie && document.cookie != '') {
                var cookies = document.cookie.split(';');
                for (var i = 0; i < cookies.length; i++) {
                    var cookie = $.trim(cookies[i]);
                    // Does this cookie string begin with the name we want?
                    if (cookie.substring(0, name.length + 1) == (name + '=')) {
                        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                        break;
                    }
                }
            }
            return cookieValue;
        }

        /* PORTIONS ADAPTED FROM OPEN SOURCE:
            Adapted from embedded source in Django MPTT:
              FeinCMS Drag-n-drop tree reordering.
              Based upon code by bright4 for Radiant CMS, rewritten for
              FeinCMS by Bjorn Post.
              September 2010
         */
        $.extend($.fn.feinTree = function() {
            $.each(DraggableMPTTAdmin.treeStructure, function(key, value) {
              treeNode(key).addClass('children');
            });

            $('div.drag-handle').bind('mousedown', function(event) {
                var BEFORE = 'before';
                var AFTER = 'after';
                var CHILD = 'child';
                var CHILD_PAD = DraggableMPTTAdmin.levelIndent;
                var originalRow = $(event.target).closest('tr');
                var rowHeight = originalRow.height();
                var moveTo = new Object();
                var resultListWidth = $('#result_list').width();

                $('body').addClass('dragging').disableSelection().bind('mousemove', function(event) {
                    // Remove focus
                    originalRow.blur();

                    // attach dragged item to mouse
                    var cloned = originalRow.html();
                    if($('#drag-ghost').length == 0) {
                        $('<div id="drag-ghost"></div>').appendTo('body');
                        }
                    $('#drag-ghost').html(cloned).css({
                        'top': event.pageY,
                        'left': event.pageX - 25,
                        });

                    // check on edge of screen
                    if(event.pageY+100 > $(window).height()+$(window).scrollTop()) {
                        $('html,body').stop().animate({scrollTop: $(window).scrollTop()+250 }, 500);
                        }
                    else if(event.pageY-50 < $(window).scrollTop()) {
                        $('html,body').stop().animate({scrollTop: $(window).scrollTop()-250 }, 500);
                        }

                    // check if drag-line element already exists, else append
                    if($('#drag-line').length < 1) {
                        $('body').append('<div id="drag-line"><span></span></div>');
                        }

                    // loop trough all rows
                    $('tr', originalRow.parent()).each( function(index, el) {
                        var element = $(el)
                        var top = element.offset().top

                        // Check if mouse is over a row
                        if( event.pageY >= top && event.pageY < top + rowHeight ) {
                            var target_loc = null
                            if( event.pageY >= top && event.pageY < top + rowHeight / 3 ) {
                                target_loc = BEFORE
                                }
                            else if( event.pageY >= top + rowHeight / 3 &&
                                        event.pageY < top + rowHeight * 2 / 3 ) {
                                var next = element.next();
                                // Don't allow adding children when there are some already
                                // or children are disabled
                                if( !mp.mptt_no_children && (
                                        !next.length || rowLevel( next ) <= rowLevel( element ) )) {
                                    target_loc = CHILD
                                    }
                                }
                            else if( event.pageY >= top + rowHeight * 2 / 3 &&
                                        event.pageY < top + rowHeight ) {
                                var next = element.next();
                                if( !next.length || rowLevel( next ) <= rowLevel( element ) ) {
                                    target_loc = AFTER
                                    }
                                }

                            if( target_loc ) {
                               var target_row = element
                               if( !target_valid( originalRow.find('.tree-node'),
                                                  target_row.find('.tree-node') ) ) {
                                    target_loc = false
                                    }
                                // Positioning relative to cell containing the link
                                var offset = target_row.find('th').offset()
                                var left = 4 + offset.left + rowLevel( target_row ) * CHILD_PAD
                                    + (target_loc == CHILD ? CHILD_PAD : 0)
                                $('#drag-line')
                                    .css({
                                        'width': resultListWidth - left,
                                        'left': left,
                                        'top': offset.top + (target_loc == BEFORE ? 0 : rowHeight)
                                        })
                                    .find('span').text(
                                        DraggableMPTTAdmin.messages[ target_loc ] ||
                                            'Cannot move here'
                                        )

                                // Store the found row and options
                                moveTo.hovering = target_row
                                moveTo.relativeTo = target_row
                                moveTo.side = target_loc
                                return true
                                }
                            }
                        });
                    });

                $('body').keydown(function(event) {
                    if (event.which == '27') {
                        $('#drag-line').remove();
                        $('#drag-ghost').remove();
                        $('body').removeClass('dragging').enableSelection().unbind('mousemove').unbind('mouseup');
                        event.preventDefault();
                    }
                });

                $('body').bind( 'mouseup', function() {
                    var target = moveTo.relativeTo
                    if( !target ) return

                    var cut_item = originalRow.find('.tree-node')
                    var target_item = target.find('.tree-node')

                    // Send to server if target is ok
                    if( target_valid( cut_item, target_item ) ) {
                        var child_ok = ( rowLevel( target ) >= rowLevel( target.next() ) )

                        // Determine position; default to placing after
                        var position = 'right'
                        if( moveTo.side == CHILD && child_ok ) {
                            position = 'last-child'
                            }
                        else if( moveTo.side == BEFORE ) {
                            position = 'left'
                            }

                        mp.fetch({
                            url: 'CURRENT_URL',
                            method: 'POST',
                            wait_indicator: true,
                            data: {
                                cmd: 'move_node',
                                position: position,
                                cut_item: cut_item.data('pk'),
                                pasted_on: target_item.data('pk'),
                                },
                            complete: function() {
                                window.location.reload()
                                },
                            })
                        }
                    else {
                        $('#drag-line').remove()
                        $('#drag-ghost').remove()
                        }

                    $('body')
                        .removeClass('dragging')
                        .enableSelection()
                        .unbind('mousemove').unbind('mouseup')
                    });

            });

            return this;
        });


        function target_valid( orig, target ) {
        /*
            MP_FRAMEWORK -- adapted drag and drop to screen needs
            HACK - based on known locations
        */
            // For some screens, dragging to top of list not valid
            var top_valid = true
            if( mp.url_current.indexOf('treenested') > 0 )
                top_valid = ( target.data('level') != 0 )

            // Use mptt left-right to detrmine if target is under original
            var under = ( orig.data('tree') == target.data('tree') ) &&
                            ( orig.data('left') <= target.data('left') ) &&
                            ( orig.data('right') >= target.data('right') )
            return !under && top_valid
            }


        /* Every time the user expands or collapses a part of the tree, we remember
           the current state of the tree so we can restore it on a reload. */
        function storeCollapsedNodes(nodes) {
            window.localStorage && window.localStorage.setItem(
                DraggableMPTTAdmin.storageName,
                JSON.stringify(nodes)
            );
        }

        function retrieveCollapsedNodes() {
            try {
                return JSON.parse(window.localStorage.getItem(
                    DraggableMPTTAdmin.storageName
                ));
            } catch( e ) {
                return null;
            }
        }

        function expandOrCollapseNode(item) {
            var show = true;

            if (!item.hasClass('children'))
                return;

            var itemId = item.data('pk');

            if (!isExpandedNode(itemId)) {
                item.removeClass('closed');
                markNodeAsExpanded(itemId);
            } else {
                item.addClass('closed');
                show = false;
                markNodeAsCollapsed(itemId);
            }

            storeCollapsedNodes(DraggableMPTTAdmin.collapsedNodes);

            doToggle(itemId, show);
        }

        function collapseTree() {
            var rlist = $("#result_list");
            rlist.hide();
            $('tbody tr', rlist).each(function(i, el) {
                var marker = $('.tree-node', el);
                if (marker.hasClass('children')) {
                    var itemId = marker.data('pk');
                    doToggle(itemId, false);
                    marker.addClass('closed');
                    markNodeAsCollapsed(itemId);
                }
            });
            storeCollapsedNodes(DraggableMPTTAdmin.collapsedNodes);
            rlist.show();
            return false;
        }

        function expandTree() {
            var rlist = $("#result_list");
            rlist.hide();
            $('tbody tr', rlist).each(function(i, el) {
                var marker = $('.tree-node', el);
                if (marker.hasClass('children')) {
                    var itemId = $('.tree-node', el).data('pk');
                    doToggle(itemId, true);
                    marker.removeClass('closed');
                    markNodeAsExpanded(itemId);
                }
            });
            storeCollapsedNodes([]);
            rlist.show();
            return false;
        }

        var changelistTab = function(elem, event, direction) {
            event.preventDefault();
            elem = $(elem);
            var ne = (direction > 0) ? elem.nextAll(':visible:first') : elem.prevAll(':visible:first');
            if(ne) {
                elem.attr('tabindex', -1);
                ne.attr('tabindex', '0');
                ne.focus();
            }
        };

        function keyboardNavigationHandler(event) {
            // console.log('keydown', this, event.keyCode);
            switch (event.keyCode) {
                case 40: // down
                    changelistTab(this, event, 1);
                    break;
                case 38: // up
                    changelistTab(this, event, -1);
                    break;
                case 37: // left
                case 39: // right
                    expandOrCollapseNode($(this).find('.tree-node'));
                    break;
                case 13: // return
                    window.location.assign( $('a', this).attr('href') );
                    break;
                default:
                    break;
            }
        }

        function addObjectTool(title, handler) {
            var $a = $('<a href/>');
            $a.click(handler);
            $a.text(title);
            $a.prependTo('.object-tools').wrap('<li>');
        }


    try {
        DraggableMPTTAdmin = JSON.parse(
            document.getElementById('draggable-admin-context').getAttribute('data-context'));

        addObjectTool(DraggableMPTTAdmin.messages.collapseTree, collapseTree);
        addObjectTool(DraggableMPTTAdmin.messages.expandTree, expandTree);

        // fire!
        var rlist = $("#result_list"),
            rlist_tbody = rlist.find('tbody');

        if ($('tbody tr', rlist).length > 1) {
            rlist_tbody.feinTree();

            rlist.find('.tree-node').on('click', function(event) {
                event.preventDefault();
                event.stopPropagation();

                expandOrCollapseNode($(this));
            });

            /* Enable focussing, put focus on first result, add handler for keyboard navigation */
            $('tr', rlist).attr('tabindex', -1);
            $('tbody tr:first', rlist).attr('tabindex', 0).focus();
            $('tr', rlist).keydown(keyboardNavigationHandler);

            DraggableMPTTAdmin.collapsedNodes = [];
            var storedNodes = retrieveCollapsedNodes();

            // MPF - make nodes start open
            if( storedNodes ) {
                for( var i=0; i<storedNodes.length; i++ ) {
                    expandOrCollapseNode(treeNode(storedNodes[i]));
                    }
                }
        }

    } catch( e ) {
        mp.log_error("Exception mptt dragable: ", e)
        }

    })

});
