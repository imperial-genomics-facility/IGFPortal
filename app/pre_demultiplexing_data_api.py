import os, logging, hashlib, shutil, gzip, tempfile
from datetime import datetime
from flask_appbuilder import ModelRestApi
from flask import request
from flask_appbuilder.api import expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db, app, celery
from .models import PreDeMultiplexingData

"""
    Pre-demultiplexing data Api
"""
log = logging.getLogger(__name__)

def load_predemult_report(
        run_name: str,
        tag_name: str,
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
            f"{run_name}{tag_name}{file_name}{datetime_str}"
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
            predemult_entry = \
                PreDeMultiplexingData(
                    run_name=run_name,
                    samplesheet_tag=tag_name,
                    file_path=target_file_path,
                    date_stamp=datestamp
                )
            db.session.add(predemult_entry)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
            raise ValueError(
                f"Failed to load pre-demult report to db, error: {e}")


@celery.task(bind=True)
def async_load_predemult_report(
        self,
        run_name: str,
        tag_name: str,
        file_path: str,
        base_path: str) -> dict:
    try:
        load_predemult_report(
            run_name=run_name,
            tag_name=tag_name,
            file_path=file_path,
            base_path=base_path)
        return {"message": "success"}
    except Exception as e:
        log.error(
            "Failed to run celery job, error: {0}".\
                format(e))


class PreDeMultiplexingDataApi(ModelRestApi):
    resource_name = "predemultiplexing_data"
    datamodel = SQLAInterface(PreDeMultiplexingData)

    @expose('/add_report',  methods=['POST'])
    @protect()
    def add_report(self):
        try:
            log.warn('received_res')
            log.warn(f"Files: {request.files}")
            log.warn(f"Data: {request.data}")
            log.warn(f"Form: {request.form}")
            if not request.files:
                return self.response_400('No files')
            json_data = request.form
            run_name = json_data.get('run_name')
            samplesheet_tag = json_data.get('samplesheet_tag')
            if run_name is None or \
               samplesheet_tag is None:
                return self.response_400('Missing run_name or samplesheet_tag')
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
                async_load_predemult_report.\
                    apply_async(args=[
                        run_name,
                        samplesheet_tag,
                        report_file,
                        base_dir])
            return self.response(200, message=f'successfully submitted demult report loading job for {os.path.basename(report_file)}')
        except Exception as e:
            log.error(e)
            return self.response_500('failed to load file')


# def search_predemultiplexing_data(run_name, samplesheet_tag):
#     try:
#         result = \
#             db.session.\
#             query(PreDeMultiplexingData).\
#             filter(PreDeMultiplexingData.run_name==run_name).\
#             filter(PreDeMultiplexingData.samplesheet_tag==samplesheet_tag).\
#             one_or_none()
#         return result
#     except Exception as e:
#         raise ValueError(
#                 "Failed to search pre demultiplexing data, error: {0}".\
#                     format(e))


# def add_predemultiplexing_data(data):
#     try:
#         if isinstance(data, bytes):
#             data = json.loads(data.decode())
#         if isinstance(data, str):
#             data = json.loads(data)
#         flowcell_cluster_plot = data.get("flowcell_cluster_plot")
#         if isinstance(flowcell_cluster_plot, dict):
#             flowcell_cluster_plot = json.dumps(flowcell_cluster_plot)
#         project_summary_table = data.get("project_summary_table")
#         if isinstance(project_summary_table, dict):
#             project_summary_table = json.dumps(project_summary_table)
#         project_summary_plot = data.get("project_summary_plot")
#         if isinstance(project_summary_plot, dict):
#             project_summary_plot = json.dumps(project_summary_plot)
#         sample_table = data.get("sample_table")
#         if isinstance(sample_table, dict):
#             sample_table = json.dumps(sample_table)
#         sample_plot = data.get("sample_plot")
#         if isinstance(sample_plot, dict):
#             sample_plot = json.dumps(sample_plot)
#         undetermined_table = data.get("undetermined_table")
#         if isinstance(undetermined_table, dict):
#             undetermined_table = json.dumps(undetermined_table)
#         undetermined_plot = data.get("undetermined_plot")
#         if isinstance(undetermined_plot, dict):
#             undetermined_plot = json.dumps(undetermined_plot)
#         predemult_data = \
#             PreDeMultiplexingData(
#                 run_name=data.get("run_name"),
#                 samplesheet_tag=data.get("samplesheet_tag"),
#                 flowcell_cluster_plot=flowcell_cluster_plot,
#                 project_summary_table=project_summary_table,
#                 project_summary_plot=project_summary_plot,
#                 sample_table=sample_table,
#                 sample_plot=sample_plot,
#                 undetermined_table=undetermined_table,
#                 undetermined_plot=undetermined_plot)
#         try:
#             db.session.add(predemult_data)
#             db.session.flush()
#             db.session.commit()
#         except:
#             db.session.rollback()
#             raise
#     except Exception as e:
#         raise ValueError(
#                 "Failed to add de-multiplex data, error: {0}".\
#                     format(e))

# def edit_predemultiplexing_data(data):
#     try:
#         if isinstance(data, bytes):
#             data = json.loads(data.decode())
#         if isinstance(data, str):
#             data = json.loads(data)
#         if "run_name" not in data:
#             raise ValueError("Missing run name")
#         if "samplesheet_tag" not in data:
#             raise ValueError("Missing sampleshheet tag")
#         flowcell_cluster_plot = data.get("flowcell_cluster_plot")
#         if flowcell_cluster_plot is not None and \
#            isinstance(flowcell_cluster_plot, dict):
#             flowcell_cluster_plot = json.dumps(flowcell_cluster_plot)
#             data.update({"flowcell_cluster_plot": flowcell_cluster_plot})
#         project_summary_table = data.get("project_summary_table")
#         if project_summary_table is not None and \
#            isinstance(project_summary_table, dict):
#             project_summary_table = json.dumps(project_summary_table)
#             data.update({"project_summary_table": project_summary_table})
#         project_summary_plot = data.get("project_summary_plot")
#         if project_summary_plot is not None and \
#            isinstance(project_summary_plot, dict):
#             project_summary_plot = json.dumps(project_summary_plot)
#             data.update({"project_summary_plot": project_summary_plot})
#         sample_table = data.get("sample_table")
#         if sample_table is not None and \
#            isinstance(sample_table, dict):
#             sample_table = json.dumps(sample_table)
#             data.update({"sample_table": sample_table})
#         sample_plot = data.get("sample_plot")
#         if sample_plot is not None and \
#            isinstance(sample_plot, dict):
#             sample_plot = json.dumps(sample_plot)
#             data.update({"sample_plot": sample_plot})
#         undetermined_table = data.get("undetermined_table")
#         if undetermined_table is not None and \
#            isinstance(undetermined_table, dict):
#             undetermined_table = json.dumps(undetermined_table)
#             data.update({"undetermined_table": undetermined_table})
#         undetermined_plot = data.get("undetermined_plot")
#         if undetermined_plot is not None and \
#            isinstance(undetermined_plot, dict):
#             undetermined_plot = json.dumps(undetermined_plot)
#             data.update({"undetermined_plot": undetermined_plot})
#         try:
#             db.session.\
#                 query(PreDeMultiplexingData).\
#                 filter(PreDeMultiplexingData.run_name==data.get("run_name")).\
#                 filter(PreDeMultiplexingData.samplesheet_tag==data.get("samplesheet_tag")).\
#                 update(data)
#             db.session.commit()
#         except:
#             db.session.rollback()
#             raise
#     except Exception as e:
#         raise ValueError(
#                 "Failed to update de-multiplex data, error: {0}".\
#                     format(e))


# def add_or_edit_predemultiplexing_data(data):
#     try:
#         if isinstance(data, bytes):
#             data = json.loads(data.decode())
#         if isinstance(data, str):
#             data = json.loads(data)
#         if "run_name" not in data:
#             raise ValueError("Missing run name")
#         if "samplesheet_tag" not in data:
#             raise ValueError("Missing sampleshheet tag")
#         result = \
#             search_predemultiplexing_data(
#                 run_name=data.get("run_name"),
#                 samplesheet_tag=data.get("samplesheet_tag"))
#         if result is None:
#             add_predemultiplexing_data(data=data)
#         else:
#             edit_predemultiplexing_data(data=data)
#     except Exception as e:
#         raise ValueError(
#                 "Failed to add or update de-multiplex data, error: {0}".\
#                     format(e))


# class PreDeMultiplexingDataApi(ModelRestApi):
#     resource_name = "predemultiplexing_data"
#     datamodel = SQLAInterface(PreDeMultiplexingData)

    # @expose('/add_or_edit_report',  methods=['POST'])
    # @protect()
    # def add_or_edit_demult_report(self):
    #     try:
    #         if not request.files:
    #             return self.response_400('No files')
    #         file_objs = request.files.getlist('file')
    #         file_obj = file_objs[0]
    #         file_obj.seek(0)
    #         json_data = file_obj.read()
    #         add_or_edit_predemultiplexing_data(data=json_data)
    #         return self.response(200, message='successfully added or updated demult data')
    #     except Exception as e:
    #         logging.error(e)

