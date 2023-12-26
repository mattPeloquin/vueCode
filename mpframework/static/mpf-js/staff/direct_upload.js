/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Integrate S3direct into MPF
*/
(function() { 'use strict';

    mp.initialize_direct_upload = function( scope ) {
        scope = scope || document.body

        /*
            File upload completion
            There's no hook for upload complete, and no DOM event to reliably
            detect completion (because input that changes is hidden), so
            use MutationObserver.
        */
        const observer = new MutationObserver( function( mutations ){
            mutations.forEach( function( mutation ) {
                const link = mutation.target
                const path = $( link ).closest('.s3direct').find('.mp_file_url')[0]

                // Set data to save and display name without version
                const filename = path.value.split('/').pop()
                path.value = filename
                _file_name_display( link, filename )

                // Do an ajax save for usability
                if( !mp.admin_add_screen ) {
                    mp.ajax_submit_form( $( link ).closest('form') )
                    }
                })
            })

        function _file_name_display( selector ) {
            // Set filename display without version
            let filename = $( selector ).html()
            const file_segs = filename.split('__mp')
            if( file_segs.length > 1 ) {
                const fileext = filename.split('.').pop()
                filename = file_segs[0] + '.' + fileext
                }
            $( selector ).html( filename )
            }

        // Set initial name value and start observer
        $( scope ).find('.mp_file_name').each( function() {
            _file_name_display( this )
            observer.observe( this, {
                attributes: true,
                })
            })
        }

    $( document ).ready( function() {
        mp.initialize_direct_upload()
        })

    })();
