#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Shared code for HTML/Code edit widgets
    Extends the Django Textarea widget; Codemirror is always available as
    an option, while other HTML editors may be added to the widget.

    Support some convenience for working with code files including drag/drop
    to replace contents.
    Paste from clipboard no longer works as browsers have locked down.
"""
from django.forms.utils import flatatt
from django.forms.widgets import Textarea
from django.utils.safestring import mark_safe

from mpframework.common import constants as mc

from .. import log


_main_html = '''
<div id="{id}_editor" class="mp_editor">
    <div class="mp_editor_top mp_flex mp_flex_between">
        <div class="mp_flex">
            {select_controls}
            <div id="{id}_copy" class="mp_button_flat mp_tooltip"
                    title="Copy HTML to clipboard">
                Copy
                </div>
            {write_controls}
            </div>
        <div class="mp_flex">
            <div id="{id}_fullscreen" class="mp_button_flat">
                Fullscreen
                </div>
            {save_controls}
            </div>
        </div>

    <!-- Codemirror will always save content here -->
    <textarea {textarea_attrs}>{value}</textarea>

    <!-- iFrame only used with HTML wysiwyg -->
    <iframe id="{id}_html_frame" class="mp_editor_iframe mp_hidden">
        </iframe>

    <script>mp.when_ui_loaded( function codemirror_fixup() {{
        var textarea = $("#{id}")[0]
        var html_frame = $("#{id}_html_frame")[0]

        // Update with codemirror when init is ready
        var cm = false

        // Fullscreen for html frame
        $("#{id}_fullscreen").on( 'click', function(_event) {{
            $("#{id}_editor").toggleClass('mp_full')
            $("body").toggleClass( 'mp_overflow_none',
                                    $("#{id}_editor").hasClass('mp_full') )
            }})

        // Copy handler - Try the copy execCommand on the buffer
        $("#{id}_copy").on( 'click', function(_event) {{
            var copied = false
            cm.save()
            textarea.style.display = ''
            textarea.select()
            try {{
                textarea.setSelectionRange( 0, 99999 )
                copied = document.execCommand('copy')
                window.getSelection().removeAllRanges()
                mp.log_info( "Copied editor text:", copied)
                }}
            catch( e ) {{
                mp.log_error("Could not copy editor text", e)
                }}
            textarea.style.display = 'none'
            copied || cm.execCommand('selectAll')
            return false
            }})

        // Dropping file
        var drop_target = $("#{id}_dropfile")
        drop_target
            .on('drag dragstart dragend dragover dragenter dragleave drop', function(e) {{
                e.preventDefault()
                e.stopPropagation()
                }})
            .on('dragover dragenter', function() {{
                drop_target.addClass('es_theme_highlight')
                }})
            .on('dragleave dragend drop', function() {{
                drop_target.removeClass('es_theme_highlight')
                }})
            .on('drop', function(e) {{
                var reader = new FileReader()
                var first_processed = false
                reader.onload = function( evt ) {{
                    if( !first_processed ) {{
                        cm.setValue('')
                        first_processed = true
                        }}
                    cm.setValue( cm.getValue() + evt.target.result )
                    }}
                _.each( e.originalEvent.dataTransfer.files, function( file ) {{
                    if( file.type.indexOf('text') >= 0 ) {{
                        reader.readAsText( file )
                        }}
                    else {{
                        mp.dialog_error("Can only import text files.\\n" +
                            "This type is: " + file.type)
                        }}
                    }})
                }})

           {extra_script}

       }})</script>
    </div>
   '''
_write_html = '''
    <div id="{id}_dropfile" class="mp_button_flat mp_editor_code mp_tooltip mp_hidden"
            title="Drag and drop file to insert contents">
        DROP FILE
        </div>
    '''
_save_html = '''
    <div class="mp_button_flat mp_change_only mp_hidden"
            onclick="$('#mpsavecontinue').click()"
            />
        Save
        </div>
    '''

def main_editor_scripting( attrs, value, script='', select='',
                            replace=True, readonly=False ):
    write = '' if readonly else (
                    _write_html.format( id=attrs.get('id') ) if replace else '' )
    save = '' if readonly else _save_html
    return _main_html.format(
                id=attrs.get('id'),
                textarea_attrs=flatatt( attrs ),
                value=value,
                extra_script=script,
                select_controls=select,
                write_controls=write,
                save_controls=save,
                )

class mpEditorBase( Textarea ):
    """
    Base widget for using HTML editors with a TextArea that saves the result
    """

    def __init__( self, *args, **kwargs ):
        self.rows = kwargs.pop( 'rows', 40 )
        self.cols = kwargs.pop( 'cols', mc.CHAR_LEN_UI_LINE )
        self.readonly = kwargs.pop( 'readOnly', False )
        self.replace = kwargs.pop( 'replace', True )
        self.upload_args = {
            'protected': kwargs.pop( 'protected', False ),
            }
        super().__init__( *args, **kwargs )

    def render( self, name, value, attrs=None, renderer=None ):
        rv = ""
        try:
            value = "" if value is None else str( value )
            attrs = attrs or {}
            attrs.update({
                'name': name,
                'rows': self.rows,
                'cols': self.cols,
                })
            rv = self.render_editor( attrs, value, replace=self.replace,
                                     readonly=self.readonly )

            log.debug_on() and log.detail3(
                    "EDITOR RENDER: %s, %s -> %s", name, value[:50], attrs )
        except Exception:
            log.exception("HTML editor: %s", name)

        return mark_safe( rv )

    def render_editor( self, attrs, value, **kwargs ):
        return main_editor_scripting( attrs, value, **kwargs )
