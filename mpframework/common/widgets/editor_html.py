#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Widget for HTML admin editors

    This embeds both HTML AND CODE editor into a single widget, allow user
    to switch between with a shared textarea. This approach ensures the
    most robust experience for both raw HTML and wysiwyg users.
    One goal is to try to preserve human-edited HTML when round-tripping
    through the HTML editor to the code editor.

    The HTML editor instances are placed into iframes, to support
    completely isolated CSS that replicates the way the HTML will be
    displayed in iframe with controlled css.

    Using a full HTML design tool (grapes) was prototyped. Decision was made
    not to include due to problems with roundtripping (HTML was completely
    redone when designer selected), and because designer support was
    not a strong enough use case to justify supporting its complexity.
    Hooks have been left here in case an option presents in the future.

    Codemirror was chosen for all code editing.

    For HTML, pretty much everything has been prototyped including
    TinyMce 4/5, Redactor, Froala, Summernote, Trumbow.
    TinyMce4 is used for now due to balance of features and licensing;
    TinyMce5's community LGPL version may be switched to in future.

    Build tinymce 4 with
    grunt bundle --themes=modern --plugins=table,paste,image,imagetools,textcolor,colorpicker,lists,link,searchreplace,media,contextmenu
"""
from django.urls import reverse

from ..utils import json_dump
from ..utils.html_utils import textarea_px_from_attrs
from .editor import mpEditorBase
from .editor import main_editor_scripting
from .editor_code import code_editor_scripting


_select_controls = '''
    <div class="mp_flex mp_editor_select">
        <div id="{id}_toggle_text" class="mp_button_flat">
            HTML
            </div>
        <div id="{id}_toggle_design" class="mp_button_flat mp_hidden">
            Design
            </div>
        <div id="{id}_toggle_code" class="mp_button_flat">
            Code
            </div>
        </div>
    '''

_extra_script = '''

    // Text editor may be referred to as object or element depending on package
    var text_editor = false
    var text_editor_el = false

    // If present, the design editor is created when iframe is loaded
    var design_editor = false

    // Sync textarea content between editors and Codemirror, if an editor is visible
    // Code mirror starts out with the HTML and is kept up to date as the reference location
    // and will update the form's textarea on submit
    function sync_cm() {{
        if( !$( html_frame ).hasClass("mp_hidden") ) {{
            // Move HTML and CSS from designer to textarea
            if( design_editor &&
                    !$( design_editor.getContainer() ).hasClass("mp_hidden") ) {{
                design_editor.store()
                var css = design_editor.getCss()
                css = css ? '<style>' + css + '</style>' : ''
                cm.setValue( css + design_editor.getHtml() )
                }}
            // Move text from text editor
            else {{
                if( text_editor || text_editor_el ) {{
                    cm.setValue( text_editor ? text_editor.getContent() :
                                               text_editor_el.innerHTML )
                    }}
                }}
            }}
        }}
    function load_design() {{
        sync_cm()
        if( !design_editor ) return
        design_editor.setComponents( textarea.value )
        design_editor.refresh()
        }}
    function load_code() {{
        sync_cm()
        }}
    function load_text() {{
        sync_cm()
        if( text_editor ) {{
            text_editor.render()
            text_editor.setContent( textarea.value )
            }}
        else if( text_editor_el ) {{
            text_editor_el.innerHTML = textarea.value
            }}
        }}

    $( textarea ).closest('form').on('submit', function() {{
        sync_cm()
        }})

    // Manage toggling of the code vs. html editor
    function toggle( mode ) {{
        var code = ( mode === 'code' )
        var design = ( mode === 'design' )
        var text = !code && !design

        // Flow content textarea to editor as needed
        text && load_text()
        design && load_design()
        code && load_code()

        // Set frame vs codemirror
        $( html_frame ).toggleClass( 'mp_hidden', code )
        $("#{id}_codemirror").toggleClass( 'mp_hidden', !code )

        // Set items in frame
        $( html_frame.contentDocument ).find("#html_designer")
            .toggleClass( 'mp_hidden', code || text )
        $( html_frame.contentDocument ).find(".mce-container")
            .toggleClass( 'mp_hidden', code || design )

        // Set buttons
        $("#{id}_toggle_text").toggleClass( 'es_theme_current', text )
        $("#{id}_toggle_design").toggleClass( 'es_theme_current', design )
        $("#{id}_toggle_code").toggleClass( 'es_theme_current', code )
        $("#{id}_editor .mp_editor_code").toggleClass( 'mp_hidden', !code )

        mp.local_get('ui').editor{id}_mode = mode
        cm.refresh()
        }}

    $("#{id}_toggle_design").on( 'click', function() {{
            toggle('design')
            }})
    $("#{id}_toggle_code").on( 'click', function() {{
            toggle('code')
            }})
    $("#{id}_toggle_text").on( 'click', function() {{
            toggle('text')
            }})

    // Initialization once DOM ready
    $( html_frame ).ready( function() {{
        $( html_frame ).css( 'height', '{height}px' )

        html_frame.onload = function() {{
            var frame_doc = this.contentDocument

            // Get reference to editors
            text_editor = this.contentWindow.text_editor
            design_editor = this.contentWindow.design_editor
// FUTURE - for editors that use initialization on textarea element
//            text_editor_el = $( frame_doc ).find("#html_textarea")[0]

            // Setup iframe scripting that needs context from server
            _.extend( text_editor.settings, {editor_settings} )
// FUTURE - for editors that need scripting init
//            var script_init = frame_doc.createElement('script')
//            script_init.text =
//                ' tinymce.init( {editor_settings} ); '
//            frame_doc.body.appendChild( script_init )

            toggle( mp.local_get('ui').editor{id}_mode )
            }}

        // Load frame contents from url once onload in place
        html_frame.contentWindow.location.replace('{editor_url}')
        }})
    '''

class HtmlEditor( mpEditorBase ):
    """
    Widget class that replaces Textarea with HTML and script necessary
    to support the HTML editor control
    """

    def render_editor( self, attrs, value, **kwargs ):

        # Don't call reverse from widget init, as it can mess up Admin URL autodiscovery
        _upload_settings = {
            'images_upload_url': reverse( 'editor_upload_image', kwargs=self.upload_args ),
            }

        # Setup editor options in json
        editor_settings = {}
        editor_settings.update( _settings )
        editor_settings.update( _upload_settings )
        editor_settings = json_dump( editor_settings )

        _width, height = textarea_px_from_attrs( attrs )

        script = code_editor_scripting( attrs )
        script += _extra_script.format(
                        id = attrs.get('id'),
                        editor_settings = editor_settings,
                        editor_url = reverse('html_editor_frame'),
                        height = height,
                        )

        rv = main_editor_scripting( attrs, value, script=script, readonly=self.readonly,
                    select=_select_controls.format( id=attrs.get('id') ) )

        return rv

_settings = {
    }
"""
FUTURE - MCE 5 inline

    'selector': '#html_editor > .inline',
    'inline': True,
    'fixed_toolbar_container': '#html_editor > .toolbar',
    'plugins': 'image imagetools table paste',
    'branding': False,

"""
