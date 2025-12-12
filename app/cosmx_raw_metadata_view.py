import os
import logging
from typing import Tuple, Any
from app import db, celery
from flask_appbuilder.actions import action
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from flask_appbuilder.models.sqla.filters import FilterInFunction
from app.models import (
    RawCosMxMetadataBuilder,
    RawCosMxMetadataModel
)
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import redirect, flash, url_for, send_file
from app.asyncio_util import run_async
from app.file_download_util import prepare_file_for_download
from .airflow.airflow_api_utils import trigger_airflow_pipeline
from .airflow.airflow_api_utils import get_airflow_dag_id
from app.cosmx_metadata.cosmx_metadata_utils import (
    raw_user_query,
    validate_raw_cosmx_metadata_and_add_to_loader_table
)


log = logging.getLogger(__name__)

COSMX_METADATA_REGISTRATION_DAG_TAG = 'cosmx_metadata_registration_dag'

@celery.task(bind=True)
def async_validate_and_register_cosmx_metadata(self, id_list):
    try:
        results = list()
        # check for airflow dag id
        airflow_dag_id = get_airflow_dag_id(
            airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'],
            dag_tag=COSMX_METADATA_REGISTRATION_DAG_TAG
        )
        if airflow_dag_id is None:
            log.error(
                "Failed to get airflow dag id for "
                + str(COSMX_METADATA_REGISTRATION_DAG_TAG)
            )
        # validate and trigger pipeline
        for raw_cosmx_id in id_list:
            info = validate_raw_cosmx_metadata_and_add_to_loader_table(
                raw_cosmx_id=raw_cosmx_id
            )
            status, error_list, raw_cosmx_metadata_id = info
            results.append(status)
            if len(error_list) == 0:
                res = trigger_airflow_pipeline(
                    dag_id=airflow_dag_id,
                    conf_data={"raw_cosmx_metadata_id": raw_cosmx_metadata_id},
                    airflow_conf_file=os.environ['AIRFLOW_CONF_FILE']
                )
                log.info(
                    "Triggered analysis registration for "
                    + f"{raw_cosmx_metadata_id} with res {res}"
                )
        return dict(zip(id_list, results))
    except Exception as e:
        log.error(
            f"Failed to run celery job, error: {e}"
        )


def action_validate_and_register_cosmx_metadata(
    item: list[RawCosMxMetadataBuilder] | RawCosMxMetadataBuilder
) -> tuple[list[str], dict[int, Any]]:
    try:
        id_list = list()
        project_list = list()
        if item is None:
            raise ValueError("No item found")
        if isinstance(item, list):
            id_list = [i.raw_cosmx_metadata_builder_id for i in item]
            project_list = [i.cosmx_metadata_tag for i in item]
        else:
            id_list = [item.raw_cosmx_metadata_builder_id]
            project_list = [item.cosmx_metadata_tag]
        response_dict = (
            async_validate_and_register_cosmx_metadata
            .apply_async(args=[id_list])
        )
        log.info(
            f"Submitted schema validation job, status: {response_dict}"
        )
        return project_list, response_dict
    except Exception as e:
        raise ValueError(
            f"Failed to run action for json validation, error: {e}")

class RawCosMxMetadataBuilderView(ModelView):
    datamodel = SQLAInterface(RawCosMxMetadataBuilder)
    label_columns = {
        "cosmx_metadata_tag": "Project name",
        "name": "Full name",
        "email_id": "Email",
        "username": "Globus username",
        "raw_user.name": "Existing user",
        "status": "Status",
        "report": "Validation report",
    }
    list_columns = [
        "cosmx_metadata_tag",
        "status"]
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_edit",
        "can_delete"
    ]
    base_order = ("raw_cosmx_metadata_builder_id", "desc")
    base_filters = [
        ["status", FilterInFunction, lambda: ["UNKNOWN", "FAILED"]]
    ]

    add_form_extra_fields = {
        "raw_user": QuerySelectField(
            "RawIgfUser",
            query_factory=raw_user_query,
            widget=Select2Widget()
        ),
    }

    edit_form_extra_fields = {
        "raw_user": QuerySelectField(
            "RawIgfUser",
            query_factory=raw_user_query,
            widget=Select2Widget()
        )
    }

    @action(
        "register_cosmx_metadata",
        "Validate metadata",
        confirmation="Are you sure?",
        multiple=True,
        single=False,
        icon="fa-rocket")
    def register_cosmx_metadata(self, item):
        try:
            projects, _ = action_validate_and_register_cosmx_metadata(item)
            flash(
                f"Submitted jobs for {', '.join(projects)}",
                "info")
            self.update_redirect()
            return redirect(url_for('RawCosMxMetadataBuilderView.list'))
        except Exception:
            flash('Failed to validate raw cosmx metadata', 'danger')
            return redirect(url_for('RawCosMxMetadataBuilderView.list'))


@celery.task(bind=True)
def async_resubmit_cosmx_metadata(self, id_list):
    try:
        results = list()
        airflow_dag_id = get_airflow_dag_id(
            airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'],
            dag_tag=COSMX_METADATA_REGISTRATION_DAG_TAG)
        if airflow_dag_id is None:
            log.error(
                "Failed to get airflow dag id for "
                + str(COSMX_METADATA_REGISTRATION_DAG_TAG)
            )
        for raw_cosmx_id in id_list:
            res = trigger_airflow_pipeline(
                dag_id=airflow_dag_id,
                    conf_data={"raw_cosmx_metadata_id": raw_cosmx_id},
                    airflow_conf_file=os.environ['AIRFLOW_CONF_FILE']
                )
            results.append(res)
            log.info(
                "Triggered analysis registration for "
                + f"{raw_cosmx_id} with res {res}"
            )
        return dict(zip(id_list, results))
    except Exception as e:
        log.error(
            f"Failed to run celery job, error: {e}"
        )


def action_resubmit_cosmx_metadata(
    item: list[RawCosMxMetadataModel] | RawCosMxMetadataModel
) -> tuple[list[str], dict[int, Any]]:
    try:
        id_list = list()
        project_list = list()
        if item is None:
            raise ValueError("No item found")
        if isinstance(item, list):
            id_list = [i.raw_cosmx_metadata_id for i in item]
            project_list = [i.cosmx_metadata_tag for i in item]
        else:
            id_list = [item.raw_cosmx_metadata_id]
            project_list = [item.cosmx_metadata_tag]
        response_dict = (
            async_resubmit_cosmx_metadata
            .apply_async(args=[id_list])
        )
        log.info(
            f"Submitted schema validation job, status: {response_dict}"
        )
        return project_list, response_dict
    except Exception as e:
        raise ValueError(
            f"Failed to run action for json validation, error: {e}")
    

class RawCosMxMetadataModelView(ModelView):
    datamodel = SQLAInterface(RawCosMxMetadataModel)
    label_columns = {
        "cosmx_metadata_tag": "Project name",
        "status": "Status",
        "formatted_csv_data": "Metadata"
    }
    list_columns = [
        "cosmx_metadata_tag",
        "status"]
    base_permissions = [
        "can_list",
        "can_show"
    ]
    base_filters = [
        ["status", FilterInFunction, lambda: ["READY"]]
    ]

    @action(
        "resubmit_pipeline",
        "Re-submit pipeline",
        confirmation="Re-submit pipeline?",
        multiple=True,
        single=False,
        icon="fa-rocket")
    def validate_and_submit_analysis(self, item):
        try:
            project_list, _ = \
                action_resubmit_cosmx_metadata(item)
            flash(
                f"Submitted jobs for {', '.join(project_list)}",
                "info")
            self.update_redirect()
            return redirect(url_for('RawCosMxMetadataModelView.list'))
        except Exception as e:
            log.error(e)
            flash(
                'Failed to re-register cosmx metadata',
                'danger')
            return redirect(url_for('RawCosMxMetadataModelView.list'))