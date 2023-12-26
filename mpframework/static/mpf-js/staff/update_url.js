/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Code for updating URLs based on admin fields
*/
(function() { 'use strict';

    mp.update_url = function( url_fn, selector, target, defalt, name_sel, name_pre ) {

        // If a URL is typed in, updated display value, otherwise default or blank
        const source = $( selector )
        if( !source.length ) return

        defalt = defalt || ''

        function update_url( set_default ) {
            let url = ''
            let set_url = false
            // Set the url value based on current field and optional defaults
            var val = source.val() || source.text()
            if( val ) {
                url = val
                if( set_default ) {
                    defalt = val
                    }
                }
            if( url ) {
                set_url = true
                }
            else {
                url = defalt
                }
            // Optionally add different name value
            let name = url
            if( name_sel ) {
                name = $( name_sel ).val() || $( name_sel ).text()
                if( name ) {
                    name = name_pre + name
                    }
                }

            $( target ).html( url_fn( url, name ) )

            return !set_url
            }

        source.keyup( function() {
            update_url()
            })
        source.each( function( index, element ) {
            $( element ).parsley().on( 'field:validated', function() {
                update_url()
                })
            })

        return update_url( true )
        }

    })();
