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
from .models import Raw_cosmx_slide, Raw_cosmx_slide_annotation

log = logging.getLogger(__name__)

"""
    COSMX slide annotation view
"""

class RawCosmxSlideAnnotationView(ModelView):
    datamodel = SQLAInterface(Raw_cosmx_slide_annotation)
    label_columns = {
        'raw_cosmx_slide.cosmx_slide_igf_id':'Slide name',
        'status': 'Status',
        'annotation':'Annotation'}
    list_columns = [
        'raw_cosmx_slide.cosmx_slide_igf_id',
        'status',
        'annotation']
    show_columns = [
        'raw_cosmx_slide.cosmx_slide_igf_id',
        'status',
        'annotation']
    add_columns = [
        'annotation']
    edit_columns = [
        'annotation']
    base_permissions = ['can_list', 'can_show', 'can_add', 'can_edit']
    base_filters = [
        ["status", FilterInFunction, lambda: ["UNKNOWN", "PIPELINE_TRIGGERED"]]]
    base_order = ("cosmx_slide_annotation_id", "desc")