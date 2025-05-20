import os, json, logging, hashlib, shutil, gzip, tempfile
from datetime import datetime
from flask_appbuilder import ModelRestApi
from flask import request, jsonify
from flask_appbuilder.api import expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db, app, celery
from .models import CosmxSlideQCData

"""
    COSMX QC data Api
"""
log = logging.getLogger(__name__)

def load_cosmx_qc_report(
        cosmx_slide_igf_id: str,
        qc_tag: str,
        file_path: str,
        base_path: str):
    try:
        ## get date stamp
        datestamp = datetime.now()
        datetime_str = \
            datestamp.strftime("%Y%m%d_%H%M%S")
        ## get file name
        file_name = \
            os.path.basename(file_path)
        ## calculate new disk path
        hash_string = \
            f"{cosmx_slide_igf_id}{qc_tag}{file_name}{datetime_str}"
        hash_md5 = \
            hashlib.\
                md5(hash_string.encode('utf-8')).\
                hexdigest()
        ## create dir and copy report file
        target_dir = \
            os.path.join(
                base_path,
                cosmx_slide_igf_id,
                hash_md5)
        target_file_path = \
            os.path.join(
                target_dir,
                file_name)
        os.makedirs(
            target_dir,
            exist_ok=True)
        shutil.copyfile(
            file_path,
            target_file_path)
        ## update db record
        try:
            cosmx_qc_entry = \
                CosmxSlideQCData(
                    cosmx_slide_igf_id=cosmx_slide_igf_id,
                    qc_tag=qc_tag,
                    file_path=target_file_path,
                    date_stamp=datestamp
                )
            db.session.add(cosmx_qc_entry)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
            raise ValueError(
                f"Failed to load cosmx qc report to db, error: {e}")


@celery.task(bind=True)
def async_load_cosmx_qc_report(
        self,
        cosmx_slide_igf_id: str,
        qc_tag: str,
        file_path: str,
        base_path: str) -> dict:
    try:
        load_cosmx_qc_report(
            cosmx_slide_igf_id=cosmx_slide_igf_id,
            qc_tag=qc_tag,
            file_path=file_path,
            base_path=base_path)
        return {"message": "success"}
    except Exception as e:
        log.error(
            "Failed to run celery job, error: {0}".\
                format(e))


class CosmxSlideQCDataApi(ModelRestApi):
    resource_name = "cosmx_qc_data"
    datamodel = SQLAInterface(CosmxSlideQCData)

    @expose('/add_report',  methods=['POST'])
    @protect()
    def add_report(self):
        try:
            if not request.files:
                return self.response_400('No files')
            json_data = request.form
            cosmx_slide_igf_id = json_data.get('cosmx_slide_igf_id')
            qc_tag = json_data.get('qc_tag')
            if cosmx_slide_igf_id is None or \
               qc_tag is None:
                return self.response_400('Missing cosmx_slide_igf_id or qc_tag')
            ## get report file from request
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            file_name = file_obj.filename
            file_obj.seek(0)
            file_data = file_obj.read()
            ## report file can be gzipped
            if file_name.endswith('.gz'):
                file_data = gzip.decompress(file_data).decode('utf-8')
            ## get report file and dump it to tmp dir
            report_dir = \
                tempfile.mkdtemp(
                    dir=app.config['CELERY_WORK_DIR'],
                    prefix='report_',)
            report_file = \
                os.path.join(report_dir, file_name)
            with open(report_file, 'wb') as fp:
                fp.write(file_data)
            ## send job to celery worker
            base_dir = \
                os.path.join(
                    app.config['REPORT_UPLOAD_PATH'],
                    'predemult_reports')
            _ = \
                async_load_cosmx_qc_report.\
                    apply_async(args=[
                        cosmx_slide_igf_id,
                        qc_tag,
                        report_file,
                        base_dir])
            return self.response(200, message=f'successfully submitted cosmx qc report loading job for {os.path.basename(report_file)}')
        except Exception as e:
            log.error(e)
            return self.response_500('failed to load file')

