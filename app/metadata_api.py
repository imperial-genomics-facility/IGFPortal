from multiprocessing.sharedctypes import Value
import os, json, logging, tempfile, time, typing, gzip
from flask_appbuilder import ModelRestApi
from flask import request
from flask_appbuilder.api import BaseApi, expose, rison
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import app, db, celery
from .metadata.metadata_util import cleanup_and_load_new_data_to_metadata_tables

log = logging.getLogger(__name__)

@celery.task(bind=True)
def async_cleanup_and_load_new_data_to_metadata_tables(
    self, json_file: str) -> dict:
    try:
        cleanup_and_load_new_data_to_metadata_tables(json_file)
        return {"message": "success"}
    except Exception as e:
        log.error(
            "Failed to run celery job, error: {0}".\
                format(e))


class MetadataLoadApi(BaseApi):
    resource_name = "metadata"
    @expose('/load_metadata', methods=['POST'])
    @protect()
    def submit_cleanup_job(self):
        try:
            if not request.files:
                return self.response_400('No files')
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            file_name = file_obj.filename
            file_obj.seek(0)
            json_data = file_obj.read()
            if file_name.endswith('.gz'):
                json_data = gzip.decompress(json_data).decode('utf-8')
            if isinstance(json_data, str):
                json_data = json.loads(json_data)
            if isinstance(json_data, bytes):
                json_data = json.loads(json_data.decode('utf-8'))
            (_, json_file) = \
                tempfile.mkstemp(
                    dir=app.config['CELERY_WORK_DIR'],
                    suffix='.json',
                    prefix='metadata_',)
            with open(json_file, 'w') as fp:
                json.dump(json_data, fp)
            _ = \
                async_cleanup_and_load_new_data_to_metadata_tables.\
                    apply_async(args=[json_file])
            return self.response(200, message='successfully submitted metadata update job')
        except Exception as e:
            log.error(e)
            return self.response_500('failed to submit metadata update job')


