#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Wrap Django email sending to improve performance, scalability,
    and robustness running with SES and SQS.
"""
from django.conf import settings
from django.core.mail import send_mail
from django.template import loader
from django.utils.html import strip_tags

from .tasks import run_queue_function
from .tasks import mp_async
from . import log
from .utils.strings import truncate
from .logging.timing import mpTiming


_SUBJECT_MAX_LENGTH = 80


def send_email_user( user, template, context, **kwargs ):
    kwargs['to_emails'] = kwargs.pop( 'to_emails', [ user.email ] )
    send_email_sandbox( user.sandbox, template, context, **kwargs )

def send_email_sandbox( sandbox, template, context, **kwargs ):
    """
    Send email message to user, in one of two modes:

      1) Pass text for subject and text in template and context

      2) Pass a template that will separate subject from body,
         and renders a text-only email using strip_tags.
    """
    from_email = kwargs.pop( 'from_email', sandbox.email_support )
    to_emails = kwargs.pop( 'to_emails', None )
    to_emails = to_emails or [ sandbox.email_staff ]

    if isinstance( context, str ):
        subject = template
        body = context
        # Create subject that negates need to open email for short messages
        if len(subject) + len(body) > _SUBJECT_MAX_LENGTH:
            start_len = _SUBJECT_MAX_LENGTH - len(subject)
            message = body[:start_len]
            subject = "{} {}".format( subject, message )
    else:
        # Template-driven emails
        subject, body, html = _load_email_template( template, context )
        kwargs['html_message'] = html

    send_email( subject, body, from_email, to_emails,
                task_group=sandbox, **kwargs )


def _load_email_template( template, context ):
    """
    Load email contents from a template:
        1) Subject is contained in if-block email_subject
        2) Body is in the else block for email_subject
        3) Text-only will look reasonable after strip_tags
    """
    subject_context = context.copy()
    subject_context['email_subject'] = True
    subject = loader.render_to_string( template, subject_context ).strip()

    text_message = strip_tags(
                loader.render_to_string( template, context ).strip() )
    html_message = loader.render_to_string( template, context )

    return subject, text_message, html_message

def _format_subject( subject ):
    """
    Email subject must not contain newlines, and is also truncated
    """
    subject = truncate( subject, _SUBJECT_MAX_LENGTH )
    subject = subject.replace('\n', ' ')
    return subject

#--------------------------------------------------------------------

def send_email( subject, message, from_email, to_emails,
            priority='HI', task_group=None, **kwargs ):
    """
    All email sent by MPF passes through here.
    By default places email on SQS, which is then then loaded by SQS
    polling and executed synchronously in that thread.
    Cases have been observed where SES goes on fritz or takes a
    long time to return, so handle some retries.
    """
    subject = _format_subject( subject )
    send_trys = kwargs.get( '__email_trys', 1 )
    if send_trys > settings.EMAIL_MP_RETRYS:
        log.error_quiet("EMAIL FAILURE max retrys exceeded: %s, %s => %s",
                    from_email, to_emails, subject)
        return
    if priority == 'NOW':
        _send_email( subject, message, from_email, to_emails, **kwargs )
    else:
        log.debug("Email queuing %s: %s -> %s, %s", priority,
                    from_email, to_emails, subject)
        run_queue_function( _send_email_task, task_group,
                    subject, message, from_email, to_emails,
                    my_priority=priority, **kwargs )
@mp_async
def _send_email_task( **kwargs ):
    """
    Most email is sent from here, running as a task executed by spooler.
    Return whether the send was successful, so the poller knows whether
    to delete the message from the queue.
    """
    kwargs.pop('my_task')
    args = kwargs.pop('my_args')
    _send_email( *args, **kwargs )

def _send_email( subject, message, from_email, to_emails, **kwargs ):
    """
    AWS SES can throttle and fail in unexpected ways, so after some
    experimentation, just try to resend any exception multiple times
    This may try to send to a bad email address on sign-up multiple times,
    but is more robust than trying to guess at different scenarios.
    """
    send_trys = kwargs.pop('__email_trys', 1)
    fail = "Mail not sent"
    t = mpTiming()
    try:
        log.debug("Email sending: %s -> %s, %s", from_email, to_emails, subject)

        mail_sent = send_mail( subject, message, from_email, to_emails, **kwargs )

        if mail_sent:
            log.info2("<- %s Email sent: %s -> %s => %s (trys: %s)",
                            t, from_email, to_emails, subject, send_trys)
            return True

    except Exception as e:
        if settings.MP_TESTING:
            raise
        fail = e
    # If fail, put email on queue for another try
    log.warning_quiet("Email Failure #%s: (%s -> %s) %s => %s",
                send_trys, from_email, to_emails, subject, fail)
    kwargs['__email_trys'] = send_trys + 1
    send_email( subject, message, from_email, to_emails, **kwargs )
