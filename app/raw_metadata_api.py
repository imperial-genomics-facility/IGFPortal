import json, logging
from flask_appbuilder import ModelRestApi
from flask import request
from flask_appbuilder.api import expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db
from .models import RawMetadataModel
from .raw_metadata.raw_metadata_util import search_metadata_table_and_get_new_projects
from .raw_metadata.raw_metadata_util import parse_and_add_new_raw_metadata


class RawMetadataDataApi(ModelRestApi):
    resource_name = "rawmetadata"
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
                search_metadata_table_and_get_new_projects(data=json_data)
            return self.response(200, new_projects=','.join(new_projects))
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
            file_obj.seek(0)
            json_data = file_obj.read()
            parse_and_add_new_raw_metadata(data=json_data)
            return self.response(200, message='loaded new metadata')
        except Exception as e:
            logging.error(e)