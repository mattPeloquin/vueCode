/*--- Mesa Platform, Copyright 2021 Vueocity, LLC

    Ajax and API/REST helpers
*/
'use strict';

mp.ajax_submit_form = function( form, ajax ) {
/*
    Submit form to page endpoint
*/
    form = $( form )[0]
    ajax = _.extend( ajax || {}, {
                url: (ajax && ajax.url) || form.action || 'CURRENT_URL',
                method: 'POST',
                data: new FormData( form ),
                contentType: false,
                processData: false,
                })
    mp.fetch( ajax )
    }

mp.ajax_submit_form_api = function( form, ajax ) {
/*
    Submit form to API endpoint as json
*/
    const array = $( form ).serializeArray()
    let data = {}
    $.map( array, function( item, _i ) {
        data[ item['name'] ] = item['value']
        })
    ajax = _.extend( ajax || {}, {
                url: (ajax && ajax.url) || $( form ).attr('action'),
                method: 'POST',
                json_data: data,
                dataType: 'json',
                })
    mp.fetch( ajax )
    }

mp.ajax_submit_form_images = function( form, media_url ) {
/*
    Add update for image uploads
*/
    if( mp.options.autosave_off ) return
    $( form ).find(".mp_upload.image input[type='file']").on( 'change', function() {
        var input = this
        var prog = null
        var link = $( input ).closest('.mp_upload').find('.mp_file_link')
        mp.ajax_submit_form( form, {
            progress: function( xhr ) {
                link.find('img').hide().attr( 'src', '' )
                prog = mp.ajax_progress( xhr, link, 'progress_' + input.name )
                },
            finished: function( values ) {
                $( prog ).remove()
                mp.ajax_update_values( form, values, media_url )
                link.find('img').show()
                },
            })
        })
    }

mp.ajax_progress = function( xhr, container, id ) {
/*
    Progress indicator factory
*/
    if( xhr.upload ) {
        function _progress_width( event ) {
            var percent = 0
            if( event.lengthComputable ) {
                var position = event.loaded || event.position
                percent = Math.ceil( position / event.total * 100 )
                }
            $("#" + id + " .mp_progress_bar").css('width', + percent + "%")
            }

        xhr.upload.addEventListener( 'progress', _progress_width, true )
        container.append(
            "<div class='mp_progress_wrapper' id='" + id + "'>" +
                    "<div class='mp_progress_bar'></div></div>" )

        return $('#' + id)
        }
    }

mp.ajax_update_values = function( scope, values, media_url ) {
/*
    Dynamic update of specific UI widgets
*/
    media_url = media_url || mpurl.media_url
    _.each( values, function( value, field ) {

        // For now, only file values
        var widget = $( scope ).find("input[name='" + field + "']").closest(".mp_upload")
        widget.find(".mp_file_link").show()
        widget.find(".mp_file_name").html( value )
        var path = media_url + '/' + value
        widget.find("img").attr( 'src', path )
        widget.find("a").attr( 'href', path )

        })
    }

mp.ajax_dialog = function( url, text, method, data ) {
/*
    Shared code for simple API calls that can resolve with a popup
*/
    mp.fetch({
        url: url,
        method: method || 'GET',
        data: data || {},
        finished: function( _values ) {
            mp.dialog_open( text )
            }
        })
    }
