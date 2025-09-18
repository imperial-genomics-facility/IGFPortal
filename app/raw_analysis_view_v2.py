import logging
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from app.models import (
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2)
from app.raw_analysis.raw_analysis_util_v2 import (
    raw_project_query,
    raw_pipeline_query)

from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface

log = logging.getLogger(__name__)

class RawAnalysisTemplateV2View(ModelView):
    datamodel = SQLAInterface(RawAnalysisTemplateV2)
    label_columns = {
        "pipeline.pipeline_name": "Pipeline name",
        "template_tag": "Name",
        "template_data": "Template"
    }
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_edit",
        "can_delete"]
    base_order = ("template_id", "desc")


class RawAnalysisSchemaV2View(ModelView):
    datamodel = SQLAInterface(RawAnalysisValidationSchemaV2)
    label_columns = {
        "pipeline.pipeline_name": "Pipeline name",
        "status": "Status",
        "json_schema": "Schema"
    }
    list_columns = [
        "pipeline.pipeline_name",
        "status",
        "date_stamp"]
    show_columns = [
        "pipeline.pipeline_name",
        "status",
        "date_stamp",
        "json_schema"]
    add_columns = [
        "pipeline",
        "json_schema"]
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_delete"]
    base_order = ("raw_analysis_schema_id", "desc")

    add_form_extra_fields = {
        "pipeline": QuerySelectField(
            "Pipeline",
            query_factory=raw_pipeline_query,
            widget=Select2Widget()
        ),
    }
    edit_form_extra_fields = {
        "pipeline": QuerySelectField(
            "Pipeline",
            query_factory=raw_pipeline_query,
            widget=Select2Widget()
        )
    }