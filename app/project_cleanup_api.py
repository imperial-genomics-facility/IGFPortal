import json, logging, gzip
from yaml import load, Loader
from flask_appbuilder import ModelRestApi
from flask import request, send_file
from flask_appbuilder.api import expose, rison
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db
from flask import g
from io import BytesIO
from .models import ProjectCleanup
from .project_cleanup_view import (
    update_status_for_project_cleanup,
    parse_and_add_project_cleanup_data)

log = logging.getLogger(__name__)

class ProjectCleanupApi(ModelRestApi):
    resource_name = "project_cleanup"
    datamodel = SQLAInterface(ProjectCleanup)

    @expose('/get_project_cleanup_data/<project_cleanup_id>',  methods=['POST'])
    @protect()
    def get_project_cleanup_data(self, project_cleanup_id):
        try:
            result = \
                db.session.\
                    query(
                        ProjectCleanup.user_email,
                        ProjectCleanup.user_name,
                        ProjectCleanup.projects,
                        ProjectCleanup.status,
                        ProjectCleanup.deletion_date).\
                    filter(ProjectCleanup.project_cleanup_id==project_cleanup_id).\
                    one_or_none()
            if result is None:
                json_data = {
                    'user_email': '',
                    'user_name': '',
                    'projects': '',
                    'status': '',
                    'deletion_date': ''}
            else:
                (user_email, user_name, projects, status, deletion_date) = \
                    result
                json_data = {
                    'user_email': user_email,
                    'user_name': user_name,
                    'projects': projects,
                    'status': status,
                    'deletion_date': str(deletion_date)}
            # dump to json text
            json_data_dump = \
                json.dumps(json_data)
            output = BytesIO(json_data_dump.encode())
            output.seek(0)
            attachment_filename = \
                f"project_cleanup_{project_cleanup_id}.json"
            return send_file(output, download_name=attachment_filename, as_attachment=True)
        except Exception as e:
            log.error(e)

    @expose('/mark_user_notified/<project_cleanup_id>',  methods=['POST'])
    @protect()
    def mark_user_notified(self, project_cleanup_id):
        try:
            try:
                update_status_for_project_cleanup(
                    project_cleanup_id_list=[project_cleanup_id],
                    status='USER_NOTIFIED',
                    user_id=g.user.id)
            except Exception as e:
                log.error(e)
                return self.response(200, status='failed')
            return self.response(200, status='success')
        except Exception as e:
            log.error(e)

    @expose('/mark_db_cleanup_finished/<project_cleanup_id>',  methods=['POST'])
    @protect()
    def mark_db_cleanup_finished(self, project_cleanup_id):
        try:
            try:
                update_status_for_project_cleanup(
                    project_cleanup_id_list=[project_cleanup_id],
                    status='DB_CLEANUP_FINISHED',
                    user_id=g.user.id)
            except Exception as e:
                log.error(e)
                return self.response(200, status='failed')
            return self.response(200, status='success')
        except Exception as e:
            log.error(e)

    @expose('/add_project_cleanup_data',  methods=['POST'])
    @protect()
    def add_project_cleanup_data(self):
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
            parse_and_add_project_cleanup_data(
                data=json_data,
                user_id=g.user.id)
            return self.response(200, message='loaded new project cleanup data')
        except Exception as e:
            log.error(e)