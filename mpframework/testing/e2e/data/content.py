#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Data templates for content
    EXCLUDES Collections, which are special cased

    The data keys in these dicts should match the names for fields
    posted in the admin forms.
"""

"""
    Content data in this dict is used to create any content type; this data is
    for general metadata and functionality rather than the content.
"""
CONTENT = {

    'BANANA': {
        '_name': 'BANANA {}',
        'tag': 'banana{}',
        'text1': 'This is a bunch of {}',
        'text2': 'text2 {}',
        'text3': 'text3 {}',
        'text4': 'text4 {}',
        'image1': '{image_file}',
        },

    'ORANGE': {
        '_name': 'Orange {}',
        'text1': 'Get some juice {txt}!',
        'image1': '{image_file}',
        'image2': '{image_file}',
        },

    'APPLE': {
        '_name': 'Apple {}',
        'tag': '{}',
        'size': '{i255}',
        '_points': '{i64}',
        },

    }


"""
    Special data dict for content
    The first level of sub-dicts are the content's DB type
    Inside each the keys match fields on the admin form for that type.
"""
CONTENT_TYPES = {
    'protectedfile': {
        'content_file': '{content_file}',
        },
    'pdf': {
        },
    'video': {
        'video_file': '{video_file}',
        },
    'audio': {
        'audio_file': '{audio_file}',
        },
    'protectedpage': {
        'html': """
                <b>TEST CONTENT PAGE for {}</b>
                <hr>
                <div style="font-size: {i64}px;
                            background: rgb({i255}, {i255}, {i255});
                            color: rgba({i255}, {i255}, {i255}, {f1})"
                    This is some text: {txt}<div>
                    """,
        },
    'embed': {
        },
    'proxyapp': {
        },
    'proxylink': {
        },
    'liveevent': {
        },
    'lmsitem': {
        },
    'quiz': {
        },
    'portalitem': {
        },
    }

