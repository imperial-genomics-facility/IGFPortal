import os, logging, gzip, tempfile, hashlib, shutil
from datetime import datetime
from flask_appbuilder import ModelRestApi
from flask import request
from flask_appbuilder.api import expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import app, db, celery
from .models import IlluminaInteropData

"""
    InterOp data Api
"""

log = logging.getLogger(__name__)

def load_interop_report(
        run_name: str,
        tag: str,
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
            f"{run_name}{tag}{file_name}{datetime_str}"
        hash_md5 = \
            hashlib.\
                md5(hash_string.encode('utf-8')).\
                hexdigest()
        ## create dir and copy report file
        target_dir = \
            os.path.join(
                base_path,
                run_name,
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
            interop_entry = \
                IlluminaInteropData(
                    run_name=run_name,
                    tag=tag,
                    file_path=target_file_path,
                    date_stamp=datestamp
                )
            db.session.add(interop_entry)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
            raise ValueError(
                f"Failed to load interop report to db, error: {e}")


@celery.task(bind=True)
def async_load_interop_report(
        self,
        run_name: str,
        tag: str,
        file_path: str,
        base_path: str) -> dict:
    try:
        load_interop_report(
            run_name=run_name,
            tag=tag,
            file_path=file_path,
            base_path=base_path)
        return {"message": "success"}
    except Exception as e:
        log.error(
            "Failed to run celery job, error: {0}".\
                format(e))


class SeqrunInteropApi(ModelRestApi):
    resource_name = "interop_data"
    datamodel = SQLAInterface(IlluminaInteropData)

    @expose('/add_report',  methods=['POST'])
    @protect()
    def add_report(self):
        try:
            log.debug('received_res')
            log.debug(f"Files: {request.files}")
            log.debug(f"Data: {request.data}")
            log.debug(f"Form: {request.form}")
            if not request.files:
                return self.response_400('No files')
            json_data = request.form
            run_name = json_data.get('run_name')
            tag = json_data.get('tag')
            if run_name is None or \
               tag is None:
                return self.response_400('Missing run_name or tag')
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
                    'interop_reports')
            _ = \
                async_load_interop_report.\
                    apply_async(args=[
                        run_name,
                        tag,
                        report_file,
                        base_dir])
            return self.response(
                    200,
                    message=\
                        f'successfully submitted interop report loading job for {os.path.basename(report_file)}')
        except Exception as e:
            log.error(e)
            return self.response_500('failed to load file')

# def search_interop_for_run(run_name: str) -> Any:
#     try:
#         result = \
#             db.session.\
#             query(IlluminaInteropData).\
#             filter(IlluminaInteropData.run_name==run_name).one_or_none()
#         return result
#     except Exception as e:
#         raise ValueError("Failed lookup for interop data, error: {0}".format(e))


# def add_interop_data(run_data: Any) -> None:
#     try:
#         if isinstance(run_data, str):
#             run_data = json.loads(run_data)
#         if isinstance(run_data, bytes):
#             run_data = json.loads(run_data.decode())
#         interop_entry = \
#             IlluminaInteropData(
#                 run_name = run_data.get('run_name'),
#                 table_data = run_data.get('table_data'),
#                 flowcell_data = run_data.get('flowcell_data'),
#                 intensity_data = run_data.get('intensity_data'),
#                 cluster_count_data = run_data.get('cluster_count_data'),
#                 density_data = run_data.get('density_data'),
#                 qscore_bins_data = run_data.get('qscore_bins_data'),
#                 qscore_cycles_data = run_data.get('qscore_cycles_data'),
#                 occupied_pass_filter = run_data.get('occupied_pass_filter'))
#         try:
#             db.session.add(interop_entry)
#             db.session.flush()
#             db.session.commit()
#         except:
#             db.session.rollback()
#             raise
#     except Exception as e:
#         raise ValueError("Failed adding interop data, error: {0}".format(e))

# def edit_interop_data(run_data: Any) -> None:
#     try:
#         if isinstance(run_data, str):
#             run_data = json.loads(run_data)
#         if isinstance(run_data, bytes):
#             run_data = json.loads(run_data.decode())
#         if "run_name" not in run_data:
#             raise ValueError("Missing run name")
#         try:
#             db.session.\
#                 query(IlluminaInteropData).\
#                 filter(IlluminaInteropData.run_name==run_data.get("run_name")).\
#                 update(run_data)
#             db.session.commit()
#         except:
#             db.session.rollback()
#             raise
#     except Exception as e:
#         raise ValueError("Failed to update interop data, error: {0}".format(e))


# def add_or_edit_interop_data(run_data: Any) -> None:
#     try:
#         if isinstance(run_data, str):
#             run_data = json.loads(run_data)
#         if isinstance(run_data, bytes):
#             run_data = json.loads(run_data.decode())
#         if "run_name" not in run_data:
#             raise ValueError("Missing run name")
#         result = \
#             search_interop_for_run(
#                 run_name=run_data.get('run_name'))
#         if result is None:
#             add_interop_data(run_data=run_data)
#         else:
#             edit_interop_data(run_data=run_data)
#     except Exception as e:
#         raise ValueError("Failed to add or edit interop data, error: {0}".format(e))


# class SeqrunInteropApi(ModelRestApi):
#     resource_name = "interop_data"
#     datamodel = SQLAInterface(IlluminaInteropData)

#     @expose('/search_run')
#     @rison()
#     def search_run(self, **kwargs):
#         try:
#             if "run_name" in kwargs['rison']:
#                 message = 'EXIST'
#                 result = \
#                     search_interop_for_run(
#                         run_name=kwargs['rison']['run_name'])
#                 if result is None:
#                     message = 'NOT EXIST'
#                 return self.response(200, message=message)
#             return self.response_400(message="Please send run_name")
#         except Exception as e:
#             logging.error(e)

#     @expose('/add_run', methods=['POST'])
#     @protect()
#     def add_run(self):
#         try:
#             if not request.files:
#                 return self.response_400('No files')
#             file_objs = request.files.getlist('file')
#             file_obj = file_objs[0]
#             file_obj.seek(0)
#             run_data = file_obj.read()
#             add_interop_data(run_data=run_data)
#             return self.response(200, message='added run data')
#         except Exception as e:
#             logging.error(e)

#     @expose('/edit_run',  methods=['POST'])
#     @protect()
#     def edit_run(self):
#         try:
#             if not request.files:
#                 return self.response_400('No files')
#             file_objs = request.files.getlist('file')
#             file_obj = file_objs[0]
#             file_obj.seek(0)
#             run_data = file_obj.read()
#             edit_interop_data(run_data=run_data)
#             return self.response(200, message='updated run data')
#         except Exception as e:
#             logging.error(e)

#     @expose('/add_or_edit_run',  methods=['POST'])
#     @protect()
#     def add_or_edit_run(self):
#         try:
#             if not request.files:
#                 return self.response_400('No files')
#             file_objs = request.files.getlist('file')
#             file_obj = file_objs[0]
#             file_obj.seek(0)
#             run_data = file_obj.read()
#             add_or_edit_interop_data(run_data)
#             return self.response(200, message='successfully added or updated run data')
#         except Exception as e:
#             logging.error(e)