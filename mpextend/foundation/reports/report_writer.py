#--- Mesa Platform, Copyright 2021 Vueocity, LLC
"""
    CSV report writing support
"""
import csv
import io
from django.conf import settings
from django.http import HttpResponse

from mpframework.common import log
from mpframework.common.aws import s3
from mpframework.common.utils import join_urls
from mpframework.common.utils.file import create_local_folder
from mpframework.common.utils.http import attachment_string
from mpframework.common.deploy.paths import work_path


REPORT_STORAGE_PATH = '_reports'


def get_report_path( *args ):
    return work_path( settings.MP_PLAYPEN_STORAGE, REPORT_STORAGE_PATH, *args )


class CsvWriter:
    """
    Unicode wrapper for csv writing
    """

    def __init__( self, output ):
        self.output = output
        self.writer = csv.writer( self.output )

    def writerow( self, columns ):
        self.writer.writerow([ str( col ) for col in columns ])


def report_writer_string():
    return CsvWriter( io.StringIO() )

def get_report_file( filename ):
    """
    Open/create given report file, if exists, will append
    """
    log.debug("Creating file report: %s", filename)
    create_local_folder( get_report_path() )
    return open( get_report_path( filename ), 'a+' )

def report_writer_file( file ):
    return CsvWriter( file )

def push_report_to_s3( sandbox, filename ):
    """
    Move the report to location on S3 where it can be accessed
    """
    log.info2("Uploading report to S3: %s -> %s", sandbox, filename)
    s3key = join_urls( REPORT_STORAGE_PATH, filename )
    s3.upload_public( get_report_path( filename ), s3key )
    return s3key

def report_writer_response( request, name ):
    """
    Provide a report writer that writes directly to an HTTP response
    """
    sandbox = request.sandbox
    log.debug("Creating response report: %s -> %s", name, sandbox)
    response = HttpResponse( content_type='text/csv' )
    filename = "{}_{}_report.csv".format( sandbox.subdomain, name )
    response['content-disposition'] = attachment_string( filename )
    return CsvWriter( response )
