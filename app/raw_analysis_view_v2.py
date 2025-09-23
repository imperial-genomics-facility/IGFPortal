import logging
from app import db, celery
from flask_appbuilder.actions import action
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from flask_appbuilder.models.sqla.filters import FilterInFunction
from app.models import (
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2)
from app.raw_analysis.raw_analysis_util_v2 import (
    raw_project_query,
    raw_pipeline_query,
    validate_analysis_json_schema,
    validate_analysis_design,
    generate_analysis_template_for_analysis_id)
from typing import Union, List, Any, Dict, Tuple
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import redirect, flash, url_for, send_file
from app.asyncio_util import run_async
from app.file_download_util import prepare_file_for_download

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
            raise ValueError("No item found")
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


def action_download_json_analysis_schema(
    item: RawAnalysisValidationSchemaV2) \
        -> Tuple[str, str]:
    try:
        json_schema = item.json_schema
        if json_schema is None:
            json_schema = '{}'
        file_path = \
            run_async(prepare_file_for_download(
                file_data=json_schema.encode('utf-8'),
                file_suffix=".json"))
        pipeline_name = \
            item.pipeline.pipeline_name.encode('utf-8').decode()
        return file_path, pipeline_name
    except Exception as e:
        raise ValueError(
            f"Failed to prepare file for download, error: {e}")

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

    @action(
        "validate_json_analysis_schema",
        "Validate JSON",
        confirmation="Run validate?",
        multiple=True,
        single=False,
        icon="fa-rocket")
    def validate_json_analysis_schema(self, item):
        try:
            pipeline_list, _ = \
                action_validate_json_analysis_schema(item)
            flash(
                f"Submitted jobs for {', '.join(pipeline_list)}",
                "info")
            self.update_redirect()
            return redirect(url_for('RawAnalysisSchemaV2View.list'))
        except Exception:
            flash('Failed to validate analysis schema', 'danger')
            return redirect(url_for('RawAnalysisSchemaV2View.list'))

    @action(
        "download_json_analysis_schema",
        "Download JSON schema",
        confirmation=None,
        icon="fa-file-excel-o",
        multiple=False, single=True)
    def download_json_analysis_schema(self, item):
        try:
            file_path, pipeline_name = \
                action_download_json_analysis_schema(item)
            self.update_redirect()
            return send_file(
                file_path,
                download_name=f'{pipeline_name}_schema.json',
                as_attachment=True)
        except Exception:
            flash(
                'Failed to download analysis schema',
                'danger')
            return redirect(url_for('RawAnalysisSchemaV2View.list'))



def action_reject_raw_analysis(
    item: Union[RawAnalysisV2, List[RawAnalysisV2]],
    reject_tag: str = 'REJECTED') -> Any:
    try:
        if isinstance(item, list):
            try:
                for i in item:
                    db.session.\
                        query(RawAnalysisV2).\
                        filter(RawAnalysisV2.raw_analysis_id==i.raw_analysis_id).\
                        update({'status': reject_tag})
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
        else:
            try:
                db.session.\
                    query(RawAnalysisV2).\
                    filter(RawAnalysisV2.raw_analysis_id==item.raw_analysis_id).\
                    update({'status': reject_tag})
                db.session.commit()
            except Exception:
                db.session.rollback()
                raise
    except Exception as e:
        raise ValueError(
            f"Failed to reject raw analysis, error: {e}")

def action_download_raw_analysis_design(item: RawAnalysisV2) -> Tuple[str, str]:
    try:
        analysis_yaml = item.analysis_yaml
        if analysis_yaml is None:
            analysis_yaml = ''
        file_path = \
            run_async(prepare_file_for_download(
                file_data=analysis_yaml.encode('utf-8'),
                file_suffix=".yaml"))
        analysis_name = \
            item.analysis_name.encode('utf-8').decode()
        return file_path, analysis_name
    except Exception as e:
        raise ValueError(
            f"Failed to prepare raw analysis design, error: {e}")


def action_validate_and_submit_analysis(
    item: Union[RawAnalysisV2, List[RawAnalysisV2]]) -> \
        Tuple[List[str], Dict[str, Any]]:
    try:
        analysis_list = list()
        id_list = list()
        if isinstance(item, list):
            analysis_list = [i.analysis_name for i in item]
            id_list = [i.raw_analysis_id for i in item]
        else:
            analysis_list = [item.analysis_name]
            id_list = [item.raw_analysis_id]
        response_dict = \
            async_validate_analysis_yaml.\
                apply_async(args=[id_list])
        log.info(
            "Submitted tasks for analysis validation, " + \
            f"status: {response_dict}")
        return analysis_list, response_dict
    except Exception as e:
        raise ValueError(
            f"Failed to validate analysis design, error: {e}")


@celery.task(bind=True)
def async_validate_analysis_yaml(self, id_list):
    try:
        results = list()
        for raw_analysis_id in id_list:
            msg = \
                validate_analysis_design(
                    raw_analysis_id=raw_analysis_id)
            results.append(msg)
        return dict(zip(id_list, results))
    except Exception as e:
        log.error(
            f"Failed to run celery job, error: {e}")


def action_download_analysis_template(
        item: RawAnalysisV2) -> Tuple[str, str]:
    try:
        if item.project_id is not None and \
           item.pipeline_id is not None:
            formatted_template = \
                generate_analysis_template_for_analysis_id(
                    raw_analysis_id=item.raw_analysis_id)
            file_path = \
                run_async(prepare_file_for_download(
                    file_data=formatted_template.encode('utf-8'),
                    file_suffix=".yaml"))
            analysis_name = item.analysis_name
            return file_path, analysis_name
        else:
            raise ValueError(
                f"Missing metadata for analysis {item.raw_analysis_id}")
    except Exception as e:
        raise ValueError(
            f"Failed to generate template, error: {e}")


class RawAnalysisV2View(ModelView):
    datamodel = SQLAInterface(RawAnalysisV2)
    label_columns = {
        "analysis_name": "Analysis name",
        "project.project_igf_id": "Project name",
        "pipeline.pipeline_name": "Pipeline name",
        "status": "Status",
        "date_stamp": "Updated on",
        "analysis_yaml": "Yaml",
        "report": "Report"}
    list_columns = [
        "analysis_name",
        "project.project_igf_id",
        "pipeline.pipeline_name",
        "status",
        "date_stamp"]
    show_columns = [
        "analysis_name",
        "project.project_igf_id",
        "pipeline.pipeline_name",
        "status",
        "date_stamp",
        "analysis_yaml", 
        "report"]
    add_columns = [
        "analysis_name",
        "project",
        "pipeline",
        "analysis_yaml"]
    edit_columns = [
        "analysis_name",
        "project",
        "pipeline",
        "analysis_yaml"]
    base_filters = [
        ["status", FilterInFunction, lambda: ["UNKNOWN", "FAILED"]]]
    base_order = ("raw_analysis_id", "desc")
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_edit"]

    add_form_extra_fields = {
        "project": QuerySelectField(
            "Project",
            query_factory=raw_project_query,
            widget=Select2Widget()
        ),
        "pipeline": QuerySelectField(
            "Pipeline",
            query_factory=raw_pipeline_query,
            widget=Select2Widget()
        ),
    }
    edit_form_extra_fields = {
        "project": QuerySelectField(
            "Project",
            query_factory=raw_project_query,
            widget=Select2Widget()
        ),
        "pipeline": QuerySelectField(
            "Pipeline",
            query_factory=raw_pipeline_query,
            widget=Select2Widget()
        )
    }

    @action(
        "reject_raw_analysis",
        "Reject analysis",
        confirmation="Reject analysis design?",
        multiple=False,
        single=True,
        icon="fa-exclamation")
    def reject_raw_analysis(self, item):
        try:
            action_reject_raw_analysis(item)
            return redirect(url_for('RawAnalysisV2View.list'))
        except Exception as e:
            log.error(e)
            flash(
                'Failed to reject analysis design',
                'danger')
            return redirect(url_for('RawAnalysisV2View.list'))


    @action(
        "download_raw_analysis_design",
        "Download analysis yaml",
        confirmation=None,
        icon="fa-file-excel-o",
        multiple=False,
        single=True)
    def download_raw_analysis_design(self, item):
        try:
            file_path, analysis_name = \
                action_download_raw_analysis_design(item)
            self.update_redirect()
            return send_file(
                file_path,
                download_name=f"{analysis_name}_analysis.yaml",
                as_attachment=True)
        except Exception as e:
            flash(
                'Failed to download raw analysis',
                'danger')
            log.error(e)
            return redirect(url_for('RawAnalysisV2View.list'))

    @action(
        "validate_and_submit_analysis",
        "Validate and upload analysis",
        confirmation="Validate analysis design?",
        multiple=True,
        single=True,
        icon="fa-rocket")
    def validate_and_submit_analysis(self, item):
        try:
            analysis_list, response_dict = \
                action_validate_and_submit_analysis(item)
            flash(
                f"Submitted jobs for {', '.join(analysis_list)}",
                "info")
            self.update_redirect()
            return redirect(url_for('RawAnalysisV2View.list'))
        except Exception as e:
            log.error(e)
            flash(
                'Failed to validate analysis design',
                'danger')
            return redirect(url_for('RawAnalysisV2View.list'))

    @action(
        "template_download",
        "Analysis template",
        confirmation="Download file?",
        icon="fa-file-excel-o",
        multiple=False,
        single=True)
    def template_download(self, item):
        try:
            if item.pipeline_id is None or \
               item.project_id is None:
                flash(
                    "Failed to generate template, no project or pipeline info",
                    "danger")
                return redirect(url_for('RawAnalysisV2View.list'))
            else:
                file_path, analysis_name = \
                    action_download_analysis_template(item)
                self.update_redirect()
                return send_file(file_path, download_name=f"{analysis_name}_analysis.yaml", as_attachment=True)
        except Exception as e:
            flash("Failed to generate template", 'danger')
            log.error(e)
            return redirect(url_for('RawAnalysisV2View.list'))

class RawAnalysisQueueV2View(ModelView):
    datamodel = SQLAInterface(RawAnalysisV2)
    label_columns = {
        "analysis_name": "Analysis name",
        "project.project_igf_id": "Project name",
        "pipeline.pipeline_name": "Pipeline name",
        "status": "Status",
        "date_stamp": "Updated on",
        "analysis_yaml": "Yaml",
        "report": "Report"
    }
    list_columns = [
        "analysis_name",
        "project.project_igf_id",
        "pipeline.pipeline_name",
        "status",
        "date_stamp"]
    show_columns = [
        "analysis_name",
        "project.project_igf_id",
        "pipeline.pipeline_name",
        "status",
        "date_stamp",
        "analysis_yaml", 
        "report"]
    base_filters = [
        ["status", FilterInFunction, lambda: ["VALIDATED",]]]
    base_order = ("raw_analysis_id", "desc")
    base_permissions = [
        "can_list",
        "can_show"]