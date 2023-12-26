{%comment%}-- Mesa Platform, Copyright 2021 Vueocity, LLC

    EasyLink content connections
    Drop this into templates that need to create content Easylinks

{%endcomment%}
;(function() { 'use strict';

    mp.easylink = {

        page: function( url ) {
            return connect_html( url )
            },
        invite: function( url ) {
            return connect_html( url, null, '{% url 'login_content' '' %}' )
            },

        page_link: function( url, name ) {
            return link( url, name )
            },
        invite_link: function( url, name ) {
            return link( url, name, '{% url 'login_content' '' %}' )
            },

        facebook: function( url ) {
            return connect_html( url, u =>
                `<a target="_" href="
                    {{ MP_EXTERNAL.facebook.share_url }}${ encodeURIComponent( u ) }">
                    <img src="{{ static_url }}images/FacebookButton.png"></a>` )
            },
        twitter: function( url ) {
            return connect_html( url, u =>
                `<a target="_" href="
                    {{ MP_EXTERNAL.twitter.share_url }}${ encodeURIComponent( u ) }">
                    <img src="{{ static_url }}images/TwitterButton.png"></a>` )
            },
        linkedin: function( url ) {
            return connect_html( url, u =>
                `<a target="_" href="
                    {{ MP_EXTERNAL.linkedin.share_url }}${ encodeURIComponent( u ) }">
                    <img src="{{ static_url }}images/LinkedinButton.png"></a>` )
            },

        access_button: function( url ) {
            return connect_html( url, ( u, slug ) =>
                `${ button_start( u, slug ) } &lt;/a&gt;
                 ${ script_include }` )
            },
        access_button_image: function( url ) {
            return connect_html( url, ( u, slug ) =>
                `${ button_start( u, slug ) } ${ image_include( u ) } &lt;/a&gt;
                 ${ script_include }` )
            },
        page_button: function( url ) {
            return connect_html( url, ( u, slug ) =>
                `${ button_start( u, slug, 'es_access_page' ) } &lt;/a&gt;
                 ${ script_include }` )
            },
        page_button_image: function( url ) {
            return connect_html( url, ( u, slug ) =>
                `${ button_start( u, slug, 'es_access_page' ) }
                    ${ image_include( u ) } &lt;/a&gt;
                 ${ script_include }` )
            },

        widget_small: function( url ) {
            return connect_html( url, ( u, slug ) =>
                `${ widget( u, slug, 'es_access_small es_access_popup' ) }
                 ${ script_include }` )
            },
        widget_large: function( url ) {
            return connect_html( url, ( u, slug ) =>
                `${ widget( u, slug, 'es_access_large' ) }
                 ${ script_include }` )
            },
        }

    const button_start = ( u, slug, css ) =>
                `&lt;a href="${ u }" class="mp_access_button ${ css || '' }"
                    data-slug="${ slug }" &gt;`
    const image_include = slug =>
                `&lt;img src="{{ static_url }}public/image/${ slug }" &gt;`
    const widget = ( u, slug, css ) =>
                `&lt;iframe class="mp_access_widget ${ css || '' }"
                    data-slug="${ slug }" src="${ u }" &gt;
                    &lt;/iframe&gt;`

    const script_include = `&lt;script
                defer src="{{ static_url }}mpf-js/access_embed.js" &gt;
                &lt;/script&gt;`

    function connect_html( slug, html_fn, target ) {
        slug = slug.trim()
        target = _.trim( target || '{% url 'portal_content' '' %}' )
        let url = '{{ site.main_host_url }}' + target + slug
        if( html_fn ) {
            url = html_fn( url, slug ).replace(/\s+/g, ' ').trim()
            }
        return url
        }

    function link( url, name, target ) {
        return connect_html( url, u =>
                `<a target="_" href="${ u }">${ name || u }</a>`,
                target )
        }

    })();
