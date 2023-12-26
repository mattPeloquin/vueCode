/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Extend localStorage to provide easy per-user storage
*/
(function() { 'use strict';

    mp.local_get = function( name ) {
        try {
            const obj = localStorage.getItem( _local_name( name ) )
            return obj ? JSON.parse( obj ) : {}
            }
        catch( e ) {
            return {}
            }
        }

    mp.local_set = function( name, obj ) {
        try {
            localStorage.setItem( _local_name( name ), JSON.stringify( obj ) )
            }
        catch( e ) {}
        }

    mp.local_update = function( name, obj ) {
        let current = mp.local_get( name )
        try {
            for( var attrname in obj ) {
                current[ attrname ] = obj[ attrname ]
                }
            }
        catch( e ) {}
        mp.local_set( name, current )
        }

    mp.local_remove = function( name ) {
        localStorage.removeItem( _local_name( name ) )
        }

    function _local_name( name ) {
        return 'mp' + mp.user.id + '-' + name
        }

    })();
