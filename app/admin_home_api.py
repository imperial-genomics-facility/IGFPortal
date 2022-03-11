import logging, json, tempfile
from flask_appbuilder.api import expose
from flask_appbuilder.security.decorators import protect
from flask_appbuilder import ModelRestApi
from flask import request
from flask_appbuilder import ModelRestApi
from flask_appbuilder.models.sqla.interface import SQLAInterface
from .models import AdminHomeData
from . import app, db, celery
from .admin_home.admin_home_utils import parse_and_add_new_admin_view_data

@celery.task(bind=True)
def async_parse_and_add_new_admin_view_data(
    self, json_file: str) -> dict:
    try:
        parse_and_add_new_admin_view_data(json_file)
        return {"message": "success"}
    except Exception as e:
        logging.error(
            "Failed to run celery job, error: {0}".\
                format(e))

class AdminHomeApi(ModelRestApi):
    resource_name = "admin_home"
    datamodel = SQLAInterface(AdminHomeData)

    @expose('/update_admin_view_data',  methods=['POST'])
    @protect()
    def update_admin_view_data(self):
        try:
            if not request.files:
                return self.response_400('No files')
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            file_obj.seek(0)
            json_data = file_obj.read()
            if isinstance(json_data, bytes):
                json_data = json.loads(json_data.decode())
            (_, json_file) = \
                tempfile.mkstemp(
                    dir=app.config['CELERY_WORK_DIR'],
                    suffix='.json',
                    prefix='admin_view_',)
            async_parse_and_add_new_admin_view_data.\
                apply_async(args=[json_file])
            return self.response(200, message='loaded new data')
        except Exception as e:
            logging.error(e)