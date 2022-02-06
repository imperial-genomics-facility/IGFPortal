from flask_appbuilder import ModelView
from .models import Project, IgfUser, Seqrun, Analysis
from flask import redirect, flash
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface

class ProjectView(ModelView):
    datamodel = SQLAInterface(Project)
    label_columns = {
        "project_igf_id": "Name",
        "start_timestamp": "Created on"
    }
    list_columns = ["project_igf_id", "start_timestamp"]
    search_columns = ["project_igf_id", "start_timestamp"]
    base_permissions = ["can_list"]
    base_order = ("project_id", "desc")

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

class AnalysisView(ModelView):
    datamodel = SQLAInterface(Analysis)
    list_columns = ["analysis_name", "analysis_type", "project.project_igf_id"]
    base_permissions = ["can_list", "can_show"]
    base_order = ("analysis_id", "desc")
    @action("trigger_analysis_pipeline", "Trigger analysis pipeline", confirmation="confirm pipeline run?", icon="fa-rocket")
    def trigger_analysis_pipeline(self, item):
        id_list = list()
        analysis_list = list()
        if isinstance(item, list):
            id_list = [i.analysis_id for i in item]
            analysis_list = [i.analysis_name for i in item]
        else:
            id_list = [item.analysis_id]
            analysis_list = [item.analysis_name]
        flash("Submitted jobs for {0}".format(', '.join(analysis_list)), "info")
        self.update_redirect()
        return redirect(self.get_redirect())
