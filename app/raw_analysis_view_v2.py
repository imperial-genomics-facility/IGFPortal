import logging
from app import celery
from flask_appbuilder.actions import action
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from app.models import (
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2)
from app.raw_analysis.raw_analysis_util_v2 import (
    raw_project_query,
    raw_pipeline_query,
    validate_analysis_json_schema)
from typing import Union, List, Any, Dict, Tuple
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import redirect, flash, url_for

log = logging.getLogger(__name__)


@celery.task(bind=True)
def async_validate_analysis_schema(self, id_list):
    try:
        results = list()
        for raw_analysis_schema_id in id_list:
            msg = \
                validate_analysis_json_schema(
                    raw_analysis_schema_id=raw_analysis_schema_id)
            results.append(msg)
        return dict(zip(id_list, results))
    except Exception as e:
        log.error(
            f"Failed to run celery job, error: {e}")


def action_validate_json_analysis_schema(
    item: Union[List[Any], Any]) \
        -> Tuple[List[str], Dict[int, Any]]:
    try:
        id_list = list()
        pipeline_list = list()
        if item is None:
            raise ValueError(f"No item found")
        if isinstance(item, list):
            id_list = [i.raw_analysis_schema_id for i in item]
            pipeline_list = [i.pipeline.pipeline_name for i in item]
        else:
            id_list = [item.raw_analysis_schema_id]
            pipeline_list = [item.pipeline.pipeline_name]
        response_dict = \
            async_validate_analysis_schema.\
                apply_async(args=[id_list])
        log.info(
            f"Submitted schema validation job, status: {response_dict}")
        return pipeline_list, response_dict
    except Exception as e:
        raise ValueError(
            f"Failed to run action for json validation, error: {e}")


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

    @action("validate_json_analysis_schema", "Validate JSON", confirmation="Run validate?", multiple=True, single=False, icon="fa-rocket")
    def validate_json_analysis_schema(self, item):
        try:
            pipeline_list, _ = action_validate_json_analysis_schema(item)
            flash("Submitted jobs for {0}".format(', '.join(pipeline_list)), "info")
            self.update_redirect()
            return redirect(url_for('RawAnalysisSchemaV2View.list'))
        except:
            flash('Failed to validate analysis schema', 'danger')
            return redirect(url_for('RawAnalysisSchemaV2View.list'))