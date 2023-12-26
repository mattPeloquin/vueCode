{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Admin Changelist JS

{%endcomment%}


{#-- Filter dropdown #}
$("#mp_filters")
    .on( 'mouseenter pointerenter focusin', function() {
        $(".mp_filters_menu").removeClass("mp_hidden")
        })
    .on( 'mouseleave pointerleave focusout', function( event ) {
        if( !$( event.currentTarget ).find( event.relatedTarget ).length ) {
            setTimeout( function() {
                $(".mp_filters_menu").addClass("mp_hidden")
                }, mp.MENU_CLOSE_DELAY )
            }
        })
$(".mp_filters_item select").change( function(){
    location.href = $(this).val()
    })
