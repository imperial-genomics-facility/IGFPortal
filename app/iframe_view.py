import json
import base64
import logging
from flask import url_for
from app import cache
from flask_appbuilder.baseviews import BaseView, expose
from flask_appbuilder.security.decorators import protect, has_access
from app import db
from .models import (
    Project_analysis_info_file,
    Project_seqrun_info_file,
    Project_seqrun_info_data,
    Project_analysis_info_data,
    PreDeMultiplexingData)


log = logging.getLogger(__name__)

def get_path_for_project_seqrun_info_file(id):
    try:
        record = \
            db.session.\
                query(
                    Project_seqrun_info_file.file_path,
                    Project_seqrun_info_data.project_id).\
                join(Project_seqrun_info_data, Project_seqrun_info_data.project_seqrun_info_data_id==Project_seqrun_info_file.project_seqrun_info_data_id).\
                filter(Project_seqrun_info_file.project_seqrun_info_file_id==id).\
                one_or_none()
        if record is None:
            log.warning(f"Missing data for id {id}")
            return '', ''
        (file_path, project_id) = record
        return file_path, project_id
    except Exception as e:
        log.error(e)

def get_path_for_project_analysis_info_file(id):
    try:
        record = \
            db.session.\
                query(
                    Project_analysis_info_file.file_path,
                    Project_analysis_info_data.project_id).\
                join(Project_analysis_info_data, Project_analysis_info_data.project_analysis_info_data_id==Project_analysis_info_file.project_analysis_info_data_id).\
                filter(Project_analysis_info_file.project_analysis_info_file_id==id).\
                one_or_none()
        if record is None:
            log.warning(f"Missing data for id {id}")
            return '', ''
        (file_path, project_id) = record
        return file_path, project_id
    except Exception as e:
        log.error(e)


def get_path_for_predemult_report(id):
    try:
        record = \
            db.session.\
                query(PreDeMultiplexingData.file_path).\
                filter(PreDeMultiplexingData.demult_id==id).\
                one_or_none()
        if record is None:
            log.warning(
                f"Missing pre-demult data for id {id}")
            return ''
        (file_path,) = \
            record
        return file_path
    except Exception as e:
        raise ValueError(
            f"Failed to get report for predemult entry {id}, error: {e}")


class IFrameView(BaseView):
    route_base = "/"

    @expose("/static/rawdata/<int:id>")
    @has_access
    @cache.cached(timeout=600)
    def view_seqrun_report(self, id):
        file_path, project_id = \
            get_path_for_project_seqrun_info_file(id=id)
        project_url = \
            url_for('ProjectView.get_project_data', id=project_id)
        # return self.render_template("iframe.html", url=file_path, project_url=project_url)
        with open(file_path, 'r') as fp:
            html_data = fp.read()
        return self.render_template("iframe.html", html_data=html_data, url_link=project_url)

    @expose("/static/analysis/<int:id>")
    @has_access
    @cache.cached(timeout=600)
    def view_analysis_report(self, id):
        file_path, project_id = \
            get_path_for_project_analysis_info_file(id=id)
        project_url = \
            url_for('ProjectView.get_project_data', id=project_id)
        # return self.render_template("iframe.html", url=file_path, project_url=project_url)
        with open(file_path, 'r') as fp:
            html_data = fp.read()
        return self.render_template("iframe.html", html_data=html_data, url_link=project_url)

    @expose("/static/predemult/<int:id>")
    @has_access
    @cache.cached(timeout=600)
    def view_predemult_report(self, id):
        file_path = \
            get_path_for_predemult_report(id=id)
        url_link = \
            url_for('PreDeMultiplexingDataView.list')
        with open(file_path, 'r') as fp:
            html_data = fp.read()
        return self.render_template("iframe.html", html_data=html_data, url_link=url_link)