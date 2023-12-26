/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Shared Base ViewModel extensions
*/
(function() { 'use strict';

    _.extend( mpp.VmShared.prototype, {

        access_options: function( vm, event ) {
        /*
            Query the available ways a user could purchase content,
            even if they currently have access.
        */
            mp.fetch({
                url: mpurl.api_access_options,
                method: 'POST',
                wait_indicator: true,
                data: {
                    'id': vm.id,
                    },
                finished: function( values ) {
                    values = mp.unpack_nested_json( values )
                    mp.access_dialog( values.pas, values.accounts )
                    }
                })
            event.stopPropagation()
            },

        })

    })();
