import json, logging, gzip
from yaml import load, Loader
from flask_appbuilder import ModelRestApi
from flask import request, send_file
from flask_appbuilder.api import expose, rison
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db
from io import BytesIO
from .models import RawAnalysis

log = logging.getLogger(__name__)

class RawAnalysisApi(ModelRestApi):
    resource_name = "raw_analysis"
    datamodel = SQLAInterface(RawAnalysis)

    @expose('/search_new_analysis',  methods=['GET'])
    @protect()
    def search_new_analysis(self):
        try:
            new_analysis_list = \
                db.session.\
                    query(RawAnalysis.raw_analysis_id).\
                    filter(RawAnalysis.status=='VALIDATED').\
                    all()
            new_analysis_ids = [
                row for (row,) in new_analysis_list]
            return self.response(200, new_analysis=new_analysis_ids)
        except Exception as e:
            log.error(e)


    @expose('/get_raw_analysis_data/<raw_analysis_id>',  methods=['POST'])
    @protect()
    def get_raw_analysis_data(self, raw_analysis_id):
        try:
            result = \
                db.session.\
                    query(
                        RawAnalysis.project_id,
                        RawAnalysis.pipeline_id,
                        RawAnalysis.analysis_name,
                        RawAnalysis.analysis_yaml).\
                    filter(RawAnalysis.raw_analysis_id==raw_analysis_id).\
                    filter(RawAnalysis.status=='VALIDATED').\
                    one_or_none()
            if result is None:
                json_data = {
                    'project_id': '',
                    'pipeline_id': '',
                    'analysis_name': '',
                    'analysis_yaml': ''}
            else:
                (project_id, pipeline_id, analysis_name, analysis_yaml) = \
                    result
                # convert yaml to json
                analysis_yaml_json = \
                    load(analysis_yaml, Loader=Loader)
                json_data = {
                    'project_id': project_id,
                    'pipeline_id': pipeline_id,
                    'analysis_name': analysis_name,
                    'analysis_yaml': analysis_yaml_json}
            # dump to json text
            json_data_dump = \
                json.dumps(json_data)
            output = BytesIO(json_data_dump.encode())
            output.seek(0)
            attachment_filename = \
                f"raw_analysis_{raw_analysis_id}.json"
            return send_file(output, download_name=attachment_filename, as_attachment=True)
        except Exception as e:
            log.error(e)


    @expose('/mark_analysis_synched/<raw_analysis_id>',  methods=['POST'])
    @protect()
    def mark_analysis_synched(self, raw_analysis_id):
        try:
            result = \
                db.session.\
                    query(RawAnalysis).\
                    filter(RawAnalysis.raw_analysis_id==raw_analysis_id).\
                    filter(RawAnalysis.status=='VALIDATED').\
                    one_or_none()
            if result is None:
                # can't find any raw analysis
                return self.response(200, status='failed')
            try:
                db.session.\
                    query(RawAnalysis).\
                    filter(RawAnalysis.raw_analysis_id==raw_analysis_id).\
                    filter(RawAnalysis.status=='VALIDATED').\
                    update({
                        'raw_analysis_id': raw_analysis_id,
                        'status': 'SYNCHED'})
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                log.error(e)
                return self.response(200, status='failed')
            return self.response(200, status='success')
        except Exception as e:
            log.error(e)


    @expose('/mark_analysis_rejected/<raw_analysis_id>',  methods=['POST'])
    @protect()
    def mark_analysis_rejected(self, raw_analysis_id):
        try:
            result = \
                db.session.\
                    query(RawAnalysis).\
                    filter(RawAnalysis.raw_analysis_id==raw_analysis_id).\
                    filter(RawAnalysis.status=='VALIDATED').\
                    one_or_none()
            if result is None:
                # can't find any raw analysis
                return self.response(200, status='failed')
            try:
                db.session.\
                    query(RawAnalysis).\
                    filter(RawAnalysis.raw_analysis_id==raw_analysis_id).\
                    filter(RawAnalysis.status=='VALIDATED').\
                    update({
                        'raw_analysis_id': raw_analysis_id,
                        'status': 'REJECTED'})
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                log.error(e)
                return self.response(200, status='success')
            return self.response(200, status='failed')
        except Exception as e:
            log.error(e)