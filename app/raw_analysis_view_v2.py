import logging
from app.models import (
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2)
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface


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