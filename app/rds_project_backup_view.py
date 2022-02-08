from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from flask_appbuilder import ModelView
from .models import RDSProject_backup, Project
import logging
from flask import redirect, flash
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from . import db

def project_query():
    results = \
        db.session.\
            query(Project).\
            filter(Project.status=='ACTIVE').\
            order_by(Project.project_id.desc()).\
            limit(20).\
            all()
    return results

class RDSProjectBackupView(ModelView):
    datamodel = SQLAInterface(RDSProject_backup)
    label_columns = {
        "project": "Project name",
        "status": "Status",
        "rds_path": "RDS path",
        "date_stamp": "Updated on"
    }
    list_columns = ["project", "status", "rds_path", "date_stamp"]
    show_columns = ["project", "status", "rds_path", "date_stamp"]
    add_columns = ["project", "rds_path"]
    edit_columns = ["project", "rds_path"]
    base_order = ("rds_backup_id", "desc")
    add_form_extra_fields = {
        "project": QuerySelectField(
            "RDSProject_backup",
            query_factory=project_query,
            widget=Select2Widget()
        )
    }
    edit_form_extra_fields = {
        "project": QuerySelectField(
            "RDSProject_backup",
            query_factory=project_query,
            widget=Select2Widget()
        )
    }
    @action("transfer_rds_data", "Transfer project to RDS path", confirmation="Copy project data to RDS?", icon="fa-rocket")
    def transfer_rds_data(self, item):
        id_list = list()
        project_list = list()
        if isinstance(item, list):
            id_list = [i.project.project_id for i in item]
            project_list = [i.project.project_igf_id for i in item]
        else:
            id_list = [item.project.project_id]
            project_list = [item.project.project_igf_id]
        flash("Submitted jobs for {0}".format(', '.join(project_list)), "info")
        self.update_redirect()
        return redirect(self.get_redirect())