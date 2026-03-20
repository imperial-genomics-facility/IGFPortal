import os
import time
import logging
from datetime import datetime
from flask_appbuilder import ModelView
from .models import RawExternalSeqrun, Platform
from flask import redirect, flash, url_for
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.filters import FilterInFunction
from flask_appbuilder.models.sqla.interface import SQLAInterface
from . import db
from . import celery
from .airflow.airflow_api_utils import trigger_airflow_pipeline
from .airflow.airflow_api_utils import get_airflow_dag_id


DAG_TAG = 'register_external_seqrun_dag'

class RawExternalSeqrunView(ModelView):
    datamodel = SQLAInterface(RawExternalSeqrun)
    list_columns = []
    show_columns = []
    label_columns = {}
    edit_columns = []
    base_permissions = [
        "can_list",
        "can_show",
        "can_edit"
    ]
    base_filters = [
        ["status", FilterInFunction, lambda: ["UNKNOWN", "CHECKING"]]]
    base_order = ("raw_external_seqrun_igf_id", "desc")

    @action(
        "reject_raw_seqrun",
        "Reject run",
        confirmation="Reject?",
        multiple=False,
        single=True,
        icon="fa-exclamation"
    )
    def reject_raw_seqrun(self, item):
        pass

    @action(
        "add_raw_seqrun",
        "Add external run",
        confirmation="Add?",
        multiple=True,
        single=False,
        icon="fa-exclamation"
    )
    def add_raw_seqrun(self, item):
        pass