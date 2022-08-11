import json, logging, gzip
from flask_appbuilder import ModelRestApi
from flask import request, send_file
from flask_appbuilder.api import expose, rison
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db
from io import BytesIO
from .models import RawSeqrun
from .raw_seqrun.raw_seqrun_util import fetch_samplesheet_for_seqrun
from .raw_seqrun.raw_seqrun_util import fetch_override_cycle_for_seqrun
from .raw_seqrun.raw_seqrun_util import fetch_samplesheet_id_for_seqrun
from .raw_seqrun.raw_seqrun_util import check_and_add_new_raw_seqrun

class RawSeqrunApi(ModelRestApi):
    resource_name = "raw_seqrun"
    datamodel = SQLAInterface(RawSeqrun)

    @expose('/add_new_seqrun',  methods=['POST'])
    @protect()
    def add_new_seqrun(self):
        try:
            if not request.files:
                return self.response_400('No files found')
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            logging.warn(file_obj.filename)
            file_obj.seek(0)
            json_data = file_obj.read()
            if isinstance(json_data, bytes):
                json_data = json_data.decode('utf-8')
            json_data = json.loads(json_data)
            seqrun_id_list = json_data.get("seqrun_id_list")
            if seqrun_id_list is None:
                return self.response_400('No seqrun_id_list')
            if isinstance(seqrun_id_list, list) and \
               len(seqrun_id_list) > 0:
                check_and_add_new_raw_seqrun(
                    seqrun_id_list=seqrun_id_list)
        except Exception as e:
            logging.error(e)


    @expose('/search_run_samplesheet',  methods=['POST'])
    @protect()
    def search_run_samplesheet(self):
        try:
            if not request.files:
                return self.response_400('No files')
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            logging.warn(file_obj.filename)
            file_obj.seek(0)
            json_data = file_obj.read()
            if isinstance(json_data, bytes):
                json_data = json_data.decode('utf-8')
            json_data = json.loads(json_data)
            seqrun_id = json_data.get("seqrun_id")
            if seqrun_id is None:
                return self.response_400('No seqrun_id found')
            result = \
                fetch_samplesheet_for_seqrun(seqrun_id=seqrun_id)
            if result is None:
                return self.response(200, message='No samplesheet found')
            else:
                (tag, csv_data) = result
                tag = \
                    tag.\
                        replace(' ', '_').\
                        replace('/', '_').\
                        replace('\\', '_')
                output = BytesIO(csv_data.encode())
                output.seek(0)
                attachment_filename = f"{tag}.csv"
                return send_file(output, attachment_filename=attachment_filename, as_attachment=True)
        except Exception as e:
            logging.error(e)

    @expose('/get_run_override_cycle/<seqrun_id>',  methods=['POST'])
    @protect()
    def get_run_override_cycle(self, seqrun_id):
        try:
            result = \
                fetch_override_cycle_for_seqrun(seqrun_id=seqrun_id)
            if result is None:
                return self.response(200, override_cycle='')
            else:
                return self.response(200, override_cycle=result)
        except Exception as e:
            logging.error(e)

    @expose('/get_samplesheet_id/<seqrun_id>',  methods=['POST'])
    @protect()
    def get_samplesheet_id(self, seqrun_id):
        try:
            result = \
                fetch_samplesheet_id_for_seqrun(seqrun_id=seqrun_id)
            if result is None:
                return self.response(200, samplesheet_id='')
            else:
                return self.response(200, samplesheet_id=result)
        except Exception as e:
            logging.error(e)