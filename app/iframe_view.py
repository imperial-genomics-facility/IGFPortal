import json
import logging
from flask import url_for
from flask_appbuilder.baseviews import BaseView, expose
from flask_appbuilder.security.decorators import protect, has_access
from app import db
from .models import Project_analysis_info_file
from .models import Project_seqrun_info_file
from .models import Project_seqrun_info_data
from .models import Project_analysis_info_data
from .metadata_view import ProjectView

log = logging.getLogger(__name__)

def get_path_for_project_seqrun_info_file(id):
    try:
        (file_path, project_id) = \
            db.session.\
                query(
                    Project_seqrun_info_file.file_path,
                    Project_seqrun_info_data.project_id).\
                join(Project_seqrun_info_data, Project_seqrun_info_data.project_seqrun_info_data_id==Project_seqrun_info_file.project_seqrun_info_data_id).\
                filter(Project_seqrun_info_file.project_seqrun_info_file_id==id).\
                one_or_none()
        return file_path, project_id
    except Exception as e:
        log.error(e)

def get_path_for_project_analysis_info_file(id):
    try:
        (file_path, project_id) = \
            db.session.\
                query(
                    Project_analysis_info_file.file_path,
                    Project_analysis_info_data.project_id).\
                join(Project_analysis_info_data, Project_analysis_info_data.project_analysis_info_data_id==Project_analysis_info_file.project_analysis_info_data_id).\
                filter(Project_analysis_info_file.project_analysis_info_file_id==id).\
                one_or_none()
        return file_path, project_id
    except Exception as e:
        log.error(e)


class IFrameView(BaseView):
    route_base = "/"

    @expose("/static/<int:id>")
    @has_access
    def view_seqrun_report(self, id):
        file_path, project_id = \
            get_path_for_project_seqrun_info_file(id=id)
        project_url = \
            url_for('ProjectView.get_project_data', id=project_id)
        return self.render_template("iframe.html", url=file_path, project_url=project_url)

    @expose("/static/<int:id>")
    @has_access
    def view_analysis_report(self, id):
        file_path, project_id = \
            get_path_for_project_analysis_info_file(id=id)
        project_url = \
            url_for('ProjectView.get_project_data', id=project_id)
        return self.render_template("iframe.html", url=file_path, project_url=project_url)