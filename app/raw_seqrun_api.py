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

class RawSeqrunApi(ModelRestApi):
    resource_name = "raw_seqrun"
    datamodel = SQLAInterface(RawSeqrun)

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