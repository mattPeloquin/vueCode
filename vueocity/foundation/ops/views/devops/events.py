#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    Support raw views into event data
"""
from django.conf import settings
from django.template.response import TemplateResponse

from mpframework.common import log
from mpframework.common.view import root_only
from mpframework.common.aws.dynamo import get_dynamo_table

from mpframework.common.aws import get_client


@root_only
def query_events( request ):
    domains = []
    events = []

    # TBD, table = get_dynamo_table('events')
    client = get_client('sdb')

    if 'POST' == request.method:
        query = request.POST.get('query')

        if 'raw' not in request.POST:

            if 'user' in request.POST:
                where = "where `user_id` = '{}'".format( query )

            elif 'sandbox' in request.POST:
                where = "where `sandbox_id` = '{}'".format( query )

            elif 'event' in request.POST:
                where = "where `event` like '%{}%'".format( query )

            elif 'time' in request.POST:
                where = "where `time` like '%{}%'".format( query )

            sort = request.POST.get('sort')
            limit = request.POST.get('limit')
            if sort:
                where += " order by `{}`".format( sort )
            if limit:
                where += " limit {}".format( limit )

            query = "select * from 'prod-StudentEvent' %s" % where

        log.info2("SDB QUERY: %s", query)
        events = client.select( SelectExpression=query )

        # Reset form
        request.method = 'GET'

    else:
        if client:
            domains = client.list_domains()['DomainNames']

    return TemplateResponse( request, 'root/ops/events.html', {
                 'events_on': settings.MP_CLOUD,
                 'events': events,
                 'domains': domains,
                 })
