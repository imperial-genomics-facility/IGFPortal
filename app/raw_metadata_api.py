import json, logging
from flask_appbuilder import ModelRestApi
from flask import request
from flask_appbuilder.api import expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db
from .models import RawMetadataModel

def search_metadata_table_and_get_new_projects(data):
    try:
        if isinstance(data, bytes):
            data = json.loads(data.decode())
        if isinstance(data, str):
            data = json.loads(data)
        if "project_list" not in data or \
           not isinstance(data.get('project_list'), list):
            raise ValueError("Missing project list")
        project_list = data.get('project_list')
        existing_projects = \
            db.session.\
                query(RawMetadataModel.metadata_tag).\
                filter(RawMetadataModel.metadata_tag.in_(project_list)).\
                all()
        existing_projects = [i[0] for i in existing_projects]
        new_projects = \
            list(
                set(project_list).\
                    difference(set(existing_projects)))
        return new_projects
    except Exception as e:
        raise ValueError(
                "Failed to search for new metadata, error: {0}".format(e))


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