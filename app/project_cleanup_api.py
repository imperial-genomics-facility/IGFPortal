import json, logging, gzip
from yaml import load, Loader
from flask_appbuilder import ModelRestApi
from flask import request, send_file
from flask_appbuilder.api import expose, rison
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db
from io import BytesIO
from .models import ProjectCleanup

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