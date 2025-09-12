import os
import json
import logging
import gviz_api
from app import db
from app import cache
import pandas as pd
from flask import abort, url_for
from flask_appbuilder import ModelView
from flask_appbuilder.views import MasterDetailView
from .models import Project, IgfUser, Seqrun, Analysis, Sample
from .models import Project_info_data, Project_seqrun_info_data, Project_seqrun_info_file
from .models import Project_analysis_info_data, Project_analysis_info_file
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.baseviews import expose
from flask_appbuilder.security.decorators import has_access

log = logging.getLogger(__name__)

def convert_to_gviz_json_for_display(description, data, columns_order, output_file=None):
    '''
    A utility method for writing gviz format json file for data display using Google charts

    :param description, A dictionary for the data table description
    :param data, A list containing the data table
    :column_order, A tuple of data table column order
    :param output_file, Output filename, default None
    :returns: None if output_file name is present, or else json_data string
    '''
    try:
        data_table = gviz_api.DataTable(description)                                # load description to gviz api
        data_table.LoadData(data)                                                   # load data to gviz_api
        final_data = data_table.ToJSon(columns_order=columns_order)                 # create final data structure
        if output_file is None:
            return final_data
        else:
            with open(output_file,'w') as jf:
                jf.write(final_data)                                                # write final data to output file
            return None
    except:
        raise


def get_project_info_analysis_data(project_id):
    try:
        analysis_results = \
            db.session.query(
                Analysis.analysis_name,
                Project_analysis_info_data.analysis_tag,
                Project_analysis_info_file.file_tag,
                Project_analysis_info_file.file_path,
                Project_analysis_info_file.project_analysis_info_file_id,
            ).\
            join(Project_analysis_info_data, Analysis.analysis_id==Project_analysis_info_data.analysis_id).\
            join(Project_analysis_info_file, Project_analysis_info_data.project_analysis_info_data_id==Project_analysis_info_file.project_analysis_info_data_id).\
            filter(Project_analysis_info_data.project_id==project_id).\
            all()
        analysis_results_df = \
            pd.DataFrame(
                analysis_results,
                columns=[
                    "Analysis name",
                    "Analysis tag",
                    "File tag",
                    "file_path",
                    "file_id"])
        analysis_results_df["file_id"].\
            astype(int)
        analysis_results_df["file_id"].\
            fillna(0, inplace=True)
        analysis_results_df["Report"] = \
            analysis_results_df.\
                apply(lambda x: \
                    '<a href="' + url_for('IFrameView.view_analysis_report', id=x['file_id']) + '">' + os.path.basename(x['file_path']) + '</a>',
                    axis=1)
        analysis_results_df = \
            analysis_results_df[[
                "Analysis name",
                "Analysis tag",
                "File tag",
                "Report"
            ]]
        analysis_results_gviz = \
            convert_to_gviz_json_for_display(
                description=[(col_name, "string") for col_name in analysis_results_df.columns.tolist()],
                data=analysis_results_df.values.tolist(),
                columns_order=analysis_results_df.columns.tolist())
        return analysis_results_gviz
    except Exception as e:
        log.error(e)


def get_project_info_seqrun_data(project_id):
    try:
        seqrun_results = \
            db.session.query(
                Seqrun.seqrun_igf_id,
                Project_seqrun_info_data.lane_number,
                Project_seqrun_info_data.index_group_tag,
                Project_seqrun_info_file.file_tag,
                Project_seqrun_info_file.file_path,
                Project_seqrun_info_file.project_seqrun_info_file_id
            ).\
            join(Seqrun, Seqrun.seqrun_id==Project_seqrun_info_data.seqrun_id).\
            join(Project_info_data, Project_info_data.project_info_data_id==Project_seqrun_info_data.project_info_data_id).\
            join(Project_seqrun_info_file, Project_seqrun_info_file.project_seqrun_info_data_id==Project_seqrun_info_data.project_seqrun_info_data_id).\
            filter(Project_info_data.project_id==project_id).\
            all()
        seqrun_results_df = \
            pd.DataFrame(
                seqrun_results,
                columns=["Sequencing run",
                         "Lane number",
                         "Index group",
                         "File tag",
                         "file_path",
                         "file_id"])
        seqrun_results_df["file_id"].\
            astype(int)
        seqrun_results_df["file_id"].\
            fillna(0, inplace=True)
        seqrun_results_df["Report"] = \
            seqrun_results_df.\
                apply(lambda x: \
                    '<a href="' + url_for('IFrameView.view_seqrun_report', id=x['file_id']) + '">' + os.path.basename(x['file_path']) + '</a>',
                    axis=1)
        seqrun_results_df = \
            seqrun_results_df[[
                "Sequencing run",
                "Lane number",
                "Index group",
                "File tag",
                "Report"]]
        seqrun_results_gviz = \
            convert_to_gviz_json_for_display(
                description=[(col_name, "string") for col_name in seqrun_results_df.columns.tolist()],
                data=seqrun_results_df.values.tolist(),
                columns_order=seqrun_results_df.columns.tolist())
        return seqrun_results_gviz
    except Exception as e:
        log.error(e)


def fetch_project_info_data(project_id):
    try:
        project_igf_id = \
            db.session.query(Project).\
            filter(Project.project_id==project_id).one_or_none()
        if project_igf_id is None:
            abort(404)
        results = \
            db.session.query(Project_info_data).\
            filter(Project_info_data.project_id==project_id).one_or_none()
        if results is None:
            abort(404)
        seqrun_results_gviz = \
            get_project_info_seqrun_data(project_id=project_id)
        analysis_results_gviz = \
            get_project_info_analysis_data(project_id=project_id)
        return project_igf_id, results.sample_read_count_data, results.project_history_data, seqrun_results_gviz,analysis_results_gviz
    except Exception as e:
        log.error(e)

class ProjectView(ModelView):
    datamodel = SQLAInterface(Project)
    label_columns = {
        "project_info": "Project name",
        "status": "Status",
        "start_timestamp": "Created on"
    }
    list_columns = ["project_info", "status", "start_timestamp"]
    search_columns = ["project_igf_id", "status", "start_timestamp"]
    base_permissions = ["can_list", "can_get_project_data"]
    base_order = ("project_id", "desc")

    @expose('/project_data/<int:id>')
    @has_access
    @cache.cached(timeout=600)
    def get_project_data(self, id):
        (project_igf_id, sample_read_count_data,
         project_history_data, seqrun_results_gviz,
         analysis_results_gviz) = \
            fetch_project_info_data(project_id=id)
        sample_read_count_data = \
            json.loads(sample_read_count_data)
        #project_history_data = \
        #    json.loads(project_history_data)
        return \
            self.render_template(
                'project_info.html',
                project_igf_id=project_igf_id,
                sample_read_count_data=sample_read_count_data,
                project_history_data=project_history_data,
                seqrun_results_gviz_data=seqrun_results_gviz,
                analysis_results_gviz_data=analysis_results_gviz,
                image_height=700)

class UserView(ModelView):
    datamodel = SQLAInterface(IgfUser)
    label_columns = {
        "name": "Name",
        "email_id": "Email"
    }
    list_columns = ["name", "email_id"]
    search_columns = ["name", "email_id"]
    base_permissions = ["can_list"]
    base_order = ("user_id", "desc")

class SeqrunView(ModelView):
    datamodel = SQLAInterface(Seqrun)
    label_columns = {
        "seqrun_igf_id": "Sequencing run",
        "date_created": "Created on"
    }
    list_columns = ["seqrun_igf_id", "date_created"]
    base_permissions = ["can_list"]
    base_order = ("seqrun_id", "desc")

class SampleView(ModelView):
    datamodel = SQLAInterface(Sample, db.session)
    label_columns = {
        "project.project_igf_id": "Project",
        "sample_igf_id": "Sample_ID",
        "sample_submitter_id": "Sample_Name",
        "species_name": "Species",
        "date_created": "Created on"
    }
    list_columns = [
        "project.project_igf_id",
        "sample_igf_id",
        "sample_submitter_id",
        "species_name",
        "date_created"
    ]
    base_permissions = ["can_list"]
    base_order = ("sample_id", "desc")

class SampleProjectView(MasterDetailView):
    datamodel = SQLAInterface(Project, db.session)
    related_views = [SampleView]
    master_div_width = 4
    list_columns = ["project_igf_id"]
    label_columns = {"project_igf_id": "Project"}
    base_permissions = ["can_list"]
    base_order = ("project_id", "desc")