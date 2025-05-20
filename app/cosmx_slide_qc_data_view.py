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
from .models import CosmxSlideQCData

log = logging.getLogger(__name__)

"""
    COSMX slide QC data view
"""

class CosmxSlideQCDataView(ModelView):
    datamodel = SQLAInterface(CosmxSlideQCData)
    label_columns = {
        'cosmx_slide_igf_id':'Slide name',
        'qc_tag':'Tag',
        'date_stamp': 'Updated on',
        'report': 'Report'}
    list_columns = [
        'cosmx_slide_igf_id',
        'qc_tag',
        'date_stamp',
        'report',]
    base_permissions = ['can_list', ]
    base_order = ("date_stamp", "desc")