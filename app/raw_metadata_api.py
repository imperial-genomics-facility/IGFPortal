import json, logging, gzip
from flask_appbuilder import ModelRestApi
from flask import request, send_file
from flask_appbuilder.api import expose, rison
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db
from io import BytesIO
from .models import RawMetadataModel
from .raw_metadata.raw_metadata_util import search_metadata_table_and_get_new_projects
from .raw_metadata.raw_metadata_util import parse_and_add_new_raw_metadata

log = logging.getLogger(__name__)

class RawMetadataDataApi(ModelRestApi):
    resource_name = "raw_metadata"
    datamodel = SQLAInterface(RawMetadataModel)

    @expose('/search_new_metadata',  methods=['POST'])
    @protect()
    def search_metadata(self):
        try:
            if not request.files:
                return self.response_400('No files')
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            file_obj.seek(0)
            json_data = file_obj.read()
            new_projects = \
                search_metadata_table_and_get_new_projects(
                    data=json_data)
            if len(new_projects) > 0:
                new_projects = \
                    ','.join(new_projects)
            else:
                new_projects = ""
            return self.response(200, new_projects=new_projects)
        except Exception as e:
            logging.error(e)

    @expose('/add_metadata',  methods=['POST'])
    @protect()
    def add_raw_metadata(self):
        try:
            if not request.files:
                return self.response_400('No files')
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            file_name = file_obj.filename
            file_obj.seek(0)
            json_data = file_obj.read()
            if not json_data:
                return self.response_400('No data')
            if file_name.endswith('.gz'):
                json_data = gzip.decompress(json_data).decode('utf-8')
            parse_and_add_new_raw_metadata(data=json_data)
            return self.response(200, message='loaded new metadata')
        except Exception as e:
            logging.error(e)

    @expose('/download_ready_metadata',  methods=['GET'])
    @protect()
    def download_ready_metadata(self):
        try:
            results = \
                db.session.\
                    query(
                        RawMetadataModel.metadata_tag,
                        RawMetadataModel.formatted_csv_data).\
                    filter(RawMetadataModel.status=='READY').\
                    all()
            if len(results)==0:
                return self.response(200)
            else:
                data = dict()
                for entry in results:
                    data.update({entry[0]: entry[1]})
                data = json.dumps(data)
                output = BytesIO(data.encode())
                output.seek(0)
                return send_file(output, download_name='metadata.json', as_attachment=True)
        except Exception as e:
            logging.error(e)

    @expose('/mark_ready_metadata_as_synced',  methods=['GET'])
    @protect()
    def mark_ready_metadata_as_synced(self):
        try:
            try:
                db.session.\
                    query(RawMetadataModel).\
                    filter(RawMetadataModel.status=='READY').\
                    update({'status':'SYNCHED'})
                db.session.commit()
                return self.response(200, message='all metadata synced')
            except:
                db.session.rollback()
                raise
        except Exception as e:
            logging.error(e)
