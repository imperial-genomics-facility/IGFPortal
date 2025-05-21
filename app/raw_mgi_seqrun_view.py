import json
import logging
from typing import Any
from io import BytesIO
from app import cache
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.models.sqla.filters import FilterInFunction
from flask_appbuilder import ModelView
from flask_appbuilder.baseviews import expose
from flask import redirect, flash, url_for, send_file
from flask_appbuilder.security.decorators import protect, has_access
from . import db
from .models import RawMgiSeqrun

log = logging.getLogger(__name__)

"""
    RawMgiSeqrun  view
"""

class RawMgiSeqrunView(ModelView):
    datamodel = SQLAInterface(RawMgiSeqrun)
    label_columns = {
        'raw_mgi_seqrun_igf_id':'Run name',
        'date_stamp': 'Date',
        'run_config':'Config'}
    list_columns = [
        'raw_mgi_seqrun_igf_id',
        'date_stamp']
    show_columns = [
        'raw_cosmx_slide.cosmx_slide_igf_id',
        'raw_mgi_seqrun_igf_id',
        'date_stamp',
        'run_config']
    base_permissions = ['can_list', 'can_show']
    base_order = ("raw_mgi_seqrun_id", "desc")