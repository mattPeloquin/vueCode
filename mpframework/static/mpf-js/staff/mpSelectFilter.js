/*---
    MPF extension of SelectFilter2
    DERVIED FROM Django 4

    Adds support for populating the select box cache with options from
    the lookup API. This provides better efficiency and response
    when lists are large and works around a Chromium issue introduced
    in 2021 where boxes with more than 10K items would hang browser.
*/
(function() { 'use strict';

    const LOOKUP_MAX = 128
    const LOOKUP_DEBOUNCE = 400

    mp.init_admin_style_select = function() {

        document.querySelectorAll( 'select.selectfilter, select.selectfilterstacked' )
            .forEach( function(el) {
                const data = el.dataset
                SelectFilter.init( el.id, data.fieldName, parseInt(data.isStacked, 10) )
                })
        }

    mp.init_admin_layout_select = function() {

        document.querySelectorAll('select.filtered')
            .forEach( function(el) {
                SelectFilter.layout( el )
                })
        }

    // SelectBox.js

    window.SelectBox = {
        cache: {},
        init: function(id) {
            const box = document.getElementById(id);
            SelectBox.cache[id] = [];
            const cache = SelectBox.cache[id];
            for (const node of box.options) {
                cache.push({value: node.value, text: node.text, displayed: 1});
            }
        },
        redisplay: function(id) {
            // Repopulate HTML select box from cache
            const box = document.getElementById(id);
            const scroll_value_from_top = box.scrollTop;
            box.innerHTML = '';

            SelectBox.sort( id )

            for (const node of SelectBox.cache[id]) {
                if (node.displayed) {
                    const new_option = new Option(node.text, node.value, false, false);
                    // Shows a tooltip when hovering over the option
                    new_option.title = node.text;
                    box.appendChild(new_option);
                }
            }
            box.scrollTop = scroll_value_from_top;
        },
        filter: function(id, to_id, text) {
        /*
            Extend Django filter to include dynamic lookup
        */
            const tokens = text.toLowerCase().split(/\s+/);
            const from_box = document.getElementById(id);

            // Filter the items already in the cache, and create a list of ids
            const existing = []
            for( const node of SelectBox.cache[id] ) {
                existing.push( node.value )
                node.displayed = 1;
                const node_text = node.text.toLowerCase();
                for( const token of tokens ) {
                    if( !node_text.includes(token) ) {
                        node.displayed = 0;
                        break; // Once the first token isn't found we're done
                        }
                    }
                }

            // For select fields marked as autolookup, make call to server
            if( from_box.dataset.model && text.length > 1 &&
                    !SelectBox._filter_in_progress[id] ) {
                const url = `${ mpurl.api_autolookup }?limit=${ LOOKUP_MAX }&` +
                            `search=${ encodeURIComponent(tokens) }&` +
                            `app=${ from_box.dataset.app }&model=${ from_box.dataset.model }`
                SelectBox._filter_in_progress[id] = true
                fetch( url )
                    .then( function( response ) {
                        mp.log_highlight2("RECEIVED: " + url )
                        return response.json()
                        })
                    .then( function( data ) {
                        // Take into account current state of to box
                        for( const node of SelectBox.cache[to_id] ) {
                            if( !existing.includes( node.value ) ) {
                                existing.push( node.value )
                                }
                            }
                        // Add any new items from fetch to cache
                        if( data && data.length && data[0].id ) {
                            for( const item of data ) {
                                const item_id = item.id.toString()
                                if( !existing.includes( item_id ) ) {
                                    SelectBox.cache[id].push({
                                                value: item_id, text: item.text, displayed: 1
                                                })
                                    }
                                }
                            }
                        // Show the current state
                        SelectBox.redisplay(id);
                        SelectBox._filter_in_progress[id] = false
                        })
                }
            else {
                SelectBox.redisplay(id);
                }
        },
        _filter_in_progress: {},

        delete_from_cache: function(id, value) {
            let delete_index = null;
            const cache = SelectBox.cache[id];
            for (const [i, node] of cache.entries()) {
                if (node.value === value) {
                    delete_index = i;
                    break;
                }
            }
            cache.splice(delete_index, 1);
        },
        add_to_cache: function(id, option) {
            SelectBox.cache[id].push({value: option.value, text: option.text, displayed: 1});
        },
        cache_contains: function(id, value) {
            // Check if an item is contained in the cache
            for (const node of SelectBox.cache[id]) {
                if (node.value === value) {
                    return true;
                }
            }
            return false;
        },
        move: function(from, to) {
            const from_box = document.getElementById(from);
            for (const option of from_box.options) {
                const option_value = option.value;
                if (option.selected && SelectBox.cache_contains(from, option_value)) {
                    SelectBox.add_to_cache(to, {value: option_value, text: option.text, displayed: 1});
                    SelectBox.delete_from_cache(from, option_value);
                }
            }
            SelectBox.redisplay(from);
            SelectBox.redisplay(to);
        },
        move_all: function(from, to) {
            const from_box = document.getElementById(from);
            for (const option of from_box.options) {
                const option_value = option.value;
                if (SelectBox.cache_contains(from, option_value)) {
                    SelectBox.add_to_cache(to, {value: option_value, text: option.text, displayed: 1});
                    SelectBox.delete_from_cache(from, option_value);
                }
            }
            SelectBox.redisplay(from);
            SelectBox.redisplay(to);
        },
        sort: function(id) {
            SelectBox.cache[id].sort(function(a, b) {
                a = a.text.toLowerCase();
                b = b.text.toLowerCase();
                if (a > b) {
                    return 1;
                }
                if (a < b) {
                    return -1;
                }
                return 0;
            } );
        },
        select_all: function(id) {
            const box = document.getElementById(id);
            for (const option of box.options) {
                option.selected = true;
            }
        }
    }

    // SelectFilter2.js adaptation

    window.SelectFilter = {
        init: function( field_id, field_name, is_stacked ) {
            if (field_id.match(/__prefix__/)) {
                // Don't initialize on empty forms.
                return;
            }
            const from_box = document.getElementById(field_id);
            from_box.id += '_from'; // change its ID
            from_box.className = 'filtered';

            for (const p of from_box.parentNode.getElementsByTagName('p')) {
                if (p.classList.contains("info")) {
                    // Remove <p class="info">, because it just gets in the way.
                    from_box.parentNode.removeChild(p);
                } else if (p.classList.contains("help")) {
                    // Move help text up to the top so it isn't below the select
                    // boxes or wrapped off on the side to the right of the add
                    // button:
                    from_box.parentNode.insertBefore(p, from_box.parentNode.firstChild);
                }
            }

            // Selector container
            const selector_div = quickElement('div', from_box.parentNode)
            selector_div.className = is_stacked ? 'selector stacked' : 'selector mp_flex_line'

            // <div class="selector-available">
            const selector_available = quickElement('div', selector_div);
            selector_available.className = 'selector-available mp_flex_column';
            const title_available = quickElement('h3', selector_available,
                                                interpolate(gettext('Available %s') + ' ', [field_name]));

            const filter_search = quickElement('div', selector_available, '', 'id', field_id + '_filter')
            filter_search.className = 'selector-filter'
            filter_search.appendChild(document.createTextNode(' '))

            const filter_input = quickElement( 'input', filter_search, '',
                                                'type', 'text', 'placeholder', gettext("Search") );
            filter_input.id = field_id + '_input';

            selector_available.appendChild(from_box);
            const choose_all = quickElement('a', selector_available, gettext("Choose all"), 'title',
                        interpolate(gettext('Click to choose all %s at once.'), [field_name]), 'href', '#', 'id', field_id + '_add_all_link');
            choose_all.className = 'selector-chooseall';

            // <ul class="selector-chooser">
            const selector_chooser = quickElement('ul', selector_div)
            selector_chooser.className = 'selector-chooser'
            const add_link = quickElement('a', quickElement('li', selector_chooser),
                                            gettext(''), 'title', gettext("Choose"),
                                            'href', '#', 'id', field_id + '_add_link')
            add_link.className = 'selector-add fa fa-arrow-right'
            const remove_link = quickElement('a', quickElement('li', selector_chooser),
                                            gettext(''), 'title', gettext("Remove"),
                                            'href', '#', 'id', field_id + '_remove_link')
            remove_link.className = 'selector-remove fa fa-arrow-left'

            // <div class="selector-chosen">
            const selector_chosen = quickElement('div', selector_div);
            selector_chosen.className = 'selector-chosen mp_flex_column';
            const title_chosen = quickElement('h3', selector_chosen, interpolate(gettext('Chosen %s') + ' ', [field_name]));

            const to_box = quickElement('select', selector_chosen, '', 'id', field_id + '_to', 'multiple', '', 'size', from_box.size, 'name', from_box.name);
            to_box.className = 'filtered';
            const clear_all = quickElement('a', selector_chosen, gettext("Remove all"), 'title', interpolate(gettext('Click to remove all chosen %s at once.'), [field_name]), 'href', '#', 'id', field_id + '_remove_all_link');
            clear_all.className = 'selector-clearall';

            from_box.name = from_box.name + '_old';

            // Set up the JavaScript event handlers for the select box filter interface
            const move_selection = function(e, elem, move_func, from, to) {
                if (elem.classList.contains('active')) {
                    move_func(from, to);
                    SelectFilter.refresh_icons(field_id);
                }
                e.preventDefault();
            };
            choose_all.addEventListener('click', function(e) {
                move_selection(e, this, SelectBox.move_all, field_id + '_from', field_id + '_to');
            });
            add_link.addEventListener('click', function(e) {
                move_selection(e, this, SelectBox.move, field_id + '_from', field_id + '_to');
            });
            remove_link.addEventListener('click', function(e) {
                move_selection(e, this, SelectBox.move, field_id + '_to', field_id + '_from');
            });
            clear_all.addEventListener('click', function(e) {
                move_selection(e, this, SelectBox.move_all, field_id + '_to', field_id + '_from');
            });
            filter_input.addEventListener('keypress', function(e) {
                SelectFilter.filter_key_press(e, field_id);
            });
            filter_input.addEventListener('keyup', function(e) {
                SelectFilter.filter_key_up(e, field_id);
            });
            filter_input.addEventListener('keydown', function(e) {
                SelectFilter.filter_key_down(e, field_id);
            });
            selector_div.addEventListener('change', function(e) {
                if (e.target.tagName === 'SELECT') {
                    SelectFilter.refresh_icons(field_id);
                }
            });
            selector_div.addEventListener('dblclick', function(e) {
                if (e.target.tagName === 'OPTION') {
                    if (e.target.closest('select').id === field_id + '_to') {
                        SelectBox.move(field_id + '_to', field_id + '_from');
                    } else {
                        SelectBox.move(field_id + '_from', field_id + '_to');
                    }
                    SelectFilter.refresh_icons(field_id);
                }
            });
            from_box.closest('form').addEventListener('submit', function() {
                SelectBox.select_all(field_id + '_to');
            });
            SelectBox.init(field_id + '_from');
            SelectBox.init(field_id + '_to');
            // Move selected from_box options to to_box
            SelectBox.move(field_id + '_from', field_id + '_to');

            // Initial icon refresh
            SelectFilter.refresh_icons(field_id);
        },

        // Set height of boxes after styles have been added
        layout: function( el ) {
            const data = el.dataset
            if( data.fieldName ) {
                const field_id = 'id_' + data.fieldName.replace( ' ', '_' )
                const is_stacked = parseInt(data.isStacked, 10)
                const filter_search = document.getElementById( field_id + '_input' )
                if ( filter_search && !is_stacked ) {
                    // In horizontal mode, give the same height to the two boxes.
                    const from_box = document.getElementById( field_id + '_from' )
                    const to_box = document.getElementById( field_id + '_to' )
                    let height = filter_search.offsetHeight + from_box.offsetHeight
                    height && ( to_box.style.height = height + 'px' )
                    }
                }
        },

        any_selected: function(field) {
            // Temporarily add the required attribute and check validity.
            field.required = true;
            const any_selected = field.checkValidity();
            field.required = false;
            return any_selected;
        },
        refresh_icons: function(field_id) {
            const from = document.getElementById(field_id + '_from');
            const to = document.getElementById(field_id + '_to');
            // Active if at least one item is selected
            document.getElementById(field_id + '_add_link').classList.toggle('active', SelectFilter.any_selected(from));
            document.getElementById(field_id + '_remove_link').classList.toggle('active', SelectFilter.any_selected(to));
            // Active if the corresponding box isn't empty
            document.getElementById(field_id + '_add_all_link').classList.toggle('active', from.querySelector('option'));
            document.getElementById(field_id + '_remove_all_link').classList.toggle('active', to.querySelector('option'));
        },
        filter_key_press: function(event, field_id) {
            const from = document.getElementById(field_id + '_from');
            // don't submit form if user pressed Enter
            if ((event.which && event.which === 13) || (event.keyCode && event.keyCode === 13)) {
                from.selectedIndex = 0;
                SelectBox.move(field_id + '_from', field_id + '_to');
                from.selectedIndex = 0;
                event.preventDefault();
            }
        },
        filter_key_up: function(event, field_id) {
            const from = document.getElementById(field_id + '_from');
            const temp = from.selectedIndex;

            // Instead of reworking everything, hack filter to take the to box into
            // account to avoid putting duplicates in
            clearTimeout( SelectFilter._key_up_debounce[field_id] )
            SelectFilter._key_up_debounce[field_id] = setTimeout( function() {

                SelectBox.filter( field_id + '_from', field_id + '_to',
                    document.getElementById(field_id + '_input').value )

                }, LOOKUP_DEBOUNCE )

            from.selectedIndex = temp;
        },
        _key_up_debounce: {},

        filter_key_down: function(event, field_id) {
            const from = document.getElementById(field_id + '_from');
            // right arrow -- move across
            if ((event.which && event.which === 39) || (event.keyCode && event.keyCode === 39)) {
                const old_index = from.selectedIndex;
                SelectBox.move(field_id + '_from', field_id + '_to');
                from.selectedIndex = (old_index === from.length) ? from.length - 1 : old_index;
                return;
            }
            // down arrow -- wrap around
            if ((event.which && event.which === 40) || (event.keyCode && event.keyCode === 40)) {
                from.selectedIndex = (from.length === from.selectedIndex + 1) ? 0 : from.selectedIndex + 1;
            }
            // up arrow -- wrap around
            if ((event.which && event.which === 38) || (event.keyCode && event.keyCode === 38)) {
                from.selectedIndex = (from.selectedIndex === 0) ? from.length - 1 : from.selectedIndex - 1;
            }
        }
    }

    })();
