{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    Scripting to init chartist
    In particular, inject current theme styles for Chartist CSS, which
    won't be known until CSS resolves, so have to sample them
    after page load is complete.

    Adding the style block at this point can't be efficient for CSS, so
    don't use this in pages that will take a hit from that

{%endcomment%}
'use strict';

const theme_maps = [
    { series: 'a', class: 'es_theme_current', attr: 'background-color' },
    { series: 'b', class: 'es_theme_highlight', attr: 'background-color' },
    ]

_.each( theme_maps, function( map ) {

    const color = mp.style_get_css( map.class, map.attr )

    const style =
        `<style>
            .es_chart_container .ct-series-${ map.series }
                    :is( .ct-line, .ct-point, .ct-bar, .ct-donut, .ct-slice-pie ) {
                fill: ${ color };
                stroke: ${ color };
                }
        </style>`

    $( style ).appendTo("body")

    })
