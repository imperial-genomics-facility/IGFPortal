from flask_appbuilder import ModelView
from .models import Project, IgfUser, Seqrun
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