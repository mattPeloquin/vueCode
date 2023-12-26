/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Staff utilities
*/
(function() { 'use strict';

    mp.staff_edit = function( admin_name, id, popup, area ) {
    /*
        Returns edit url that either pops up or redirects to current location
    */
        area = area || 'mpcontent'
        const new_loc = mpurl.admin + area + '/' + admin_name + '/' + id + '/change/'
        if( popup ) {
            window.open( new_loc + '?_popup=1' )
            }
        else {
            const redirect = '?admin_redirect=' + window.location.pathname +
                        window.location.hash
            window.location.assign( new_loc + redirect )
            }
        }

    })();
