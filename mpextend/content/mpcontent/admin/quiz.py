#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Quiz admin
"""

from mpframework.common.admin import root_admin
from mpframework.common.admin import staff_admin
from mpframework.common.widgets import CodeEditor
from mpframework.common.admin import StaffAdminMixin
from mpframework.content.mpcontent.admin import BaseItemAdmin
from mpframework.content.mpcontent.admin import BaseItemForm

from ..models import Quiz


class QuizForm( BaseItemForm ):
    class Meta:
        model = Quiz
        exclude = ()

        labels = dict( BaseItemForm.Meta.labels, **{
            'content': "Quiz content",
            })
        labels_sb = dict( BaseItemForm.Meta.labels_sb, **{
            })
        help_texts = dict( BaseItemForm.Meta.help_texts, **{
            'content': "Quiz questions, answers, and options.",
            })
        widgets = dict( BaseItemForm.Meta.widgets, **{
            'content': CodeEditor( mode='yaml', rows=32 ),
            })


class QuizAdmin( BaseItemAdmin ):
    form = QuizForm

root_admin.register( Quiz, QuizAdmin )


class QuizStaffAdmin( StaffAdminMixin, QuizAdmin ):
    pass

staff_admin.register( Quiz, QuizStaffAdmin )
