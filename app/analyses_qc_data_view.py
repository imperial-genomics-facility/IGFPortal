import json
import logging
from typing import Any
from io import BytesIO
from app import cache
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView
from flask_appbuilder.baseviews import expose
from flask import redirect, flash, url_for, send_file
from flask_appbuilder.security.decorators import protect, has_access
from . import db
from .models import AnalysesQCData

log = logging.getLogger(__name__)

"""
    Analyses QC data view
"""

class AnalysesQCDataView(ModelView):
    datamodel = SQLAInterface(AnalysesQCData)
    label_columns = {
        'analysis_name':'Analyses name',
        'analysis_type': 'Pipeline',
        'qc_tag':'Tag',
        'date_stamp': 'Updated on',
        'report': 'Report'}
    list_columns = [
        'analysis_name',
        'analysis_type',
        'qc_tag',
        'date_stamp',
        'report',]
    base_permissions = ['can_list', ]
    base_order = ("date_stamp", "desc")