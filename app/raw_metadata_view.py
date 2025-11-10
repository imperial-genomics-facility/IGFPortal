import os
import logging
import pandas as pd
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.models.sqla.filters import FilterInFunction
from flask import redirect, flash, url_for, send_file
from flask_appbuilder import ModelView
from . import celery
from io import BytesIO, StringIO
from flask_appbuilder.actions import action
from .models import RawMetadataModel
from .airflow.airflow_api_utils import trigger_airflow_pipeline
from .airflow.airflow_api_utils import get_airflow_dag_id
from .raw_metadata.raw_metadata_util import (
    validate_raw_metadata_and_set_db_status,
    mark_raw_metadata_as_ready)
from . import db

log = logging.getLogger(__name__)

METADATA_REGISTRATION_DAG_TAG = 'metadata_registration_dag'

@celery.task(bind=True)
def async_validate_metadata(self, id_list):
    try:
        results = list()
        for raw_metadata_id in id_list:
            msg = \
                validate_raw_metadata_and_set_db_status(
                    raw_metadata_id=raw_metadata_id)
            if msg == 'VALIDATED':
                mark_raw_metadata_as_ready(
                    id_list=[raw_metadata_id])
                airflow_dag_id = \
                    get_airflow_dag_id(
                        airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'],
                        dag_tag=METADATA_REGISTRATION_DAG_TAG)
                if airflow_dag_id is None:
                    log.error(
                        "Failed to get airflow dag id for " +
                        METADATA_REGISTRATION_DAG_TAG)
                else:
                    res = \
                        trigger_airflow_pipeline(
                            dag_id=airflow_dag_id,
                            conf_data={"raw_metadata_id": raw_metadata_id},
                            airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'])
                    log.info(
                        "Triggered metadata registration for " + \
                        f"{raw_metadata_id} with res {res}")
            results.append(msg)
        return dict(zip(id_list, results))
    except Exception as e:
        log.error(
            "Failed to run celery job for metadata validation, " + \
            f"error: {e}")


class RawMetadataSubmitView(ModelView):
    datamodel = SQLAInterface(RawMetadataModel)
    label_columns = {
        "metadata_tag": "Tag",
        "formatted_csv_data": "CSV",
        "report": "Report",
        "status": "Status",
        "update_time": "Updated on"}
    list_columns = [
        "metadata_tag",
        "status",
        "update_time"]
    show_columns = [
        "metadata_tag",
        "formatted_csv_data",
        "report",
        "status",
        "update_time"]
    base_permissions = ["can_list", "can_show"]
    base_order = ("raw_metadata_id", "desc")
    base_filters = [
        ["status", FilterInFunction, lambda: ["READY", "VALIDATED"]]]

    @action(
        "download_validated_metadata_csv",
        "Download csv",
        confirmation=None,
        icon="fa-file-excel-o",
        multiple=False,
        single=True)
    def download_validated_metadata_csv(self, item):
        output = BytesIO()
        tag = 'Empty'
        if isinstance(item.formatted_csv_data, str) and \
           len(item.formatted_csv_data.split("\n")) > 0:
            cvsStringIO = StringIO(item.formatted_csv_data)
            df = pd.read_csv(cvsStringIO, header=0)
            df.to_csv(output, index=False)
            tag = item.metadata_tag
        else:
            df = pd.DataFrame([])
            df.to_csv(output, index=False)
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name=f"{tag}_formatted.csv", as_attachment=True)

    @action(
        "resubmit_metadata",
        "Re-upload metadata",
        confirmation="Trigger pipeline again?",
        icon="fa-rocket")
    def upload_raw_metadata_csv(self, item):
        id_list = list()
        tag_list = list()
        if isinstance(item, list):
            id_list = [i.raw_metadata_id for i in item]
            tag_list = [i.metadata_tag for i in item]
        else:
            id_list = [item.raw_metadata_id]
            tag_list = [item.metadata_tag]
        try:
            _ = \
                async_validate_metadata\
                .apply_async(args=[id_list])
            flash(
                f"Submitted jobs for {', '.join(tag_list)}",
                "info")
        except Exception as e:
            flash(
                f"Failed to submit jobs for {', '.join(tag_list)}",
                "danger")
            log.error(e)
        self.update_redirect()
        return redirect(self.get_redirect())


class RawMetadataValidationView(ModelView):
    datamodel = SQLAInterface(RawMetadataModel)
    label_columns = {
        "metadata_tag": "Tag",
        "formatted_csv_data": "CSV",
        "report": "Report",
        "status": "Status",
        "update_time": "Updated on"}
    list_columns = [
        "metadata_tag",
        "status",
        "update_time"]
    add_columns = [
        "metadata_tag",
        "formatted_csv_data"]
    edit_columns = [
        "metadata_tag",
        "formatted_csv_data"]
    show_columns = [
        "metadata_tag",
        "formatted_csv_data",
        "report",
        "status",
        "update_time"]
    base_order = ("raw_metadata_id", "desc")
    base_permissions = ["can_list", "can_show", "can_edit", "can_add"]
    base_filters = [
        ["status", FilterInFunction, lambda: ["UNKNOWN", "FAILED"]]]

    @action(
        "download_raw_metadata_csv",
        "Download csv",
        confirmation=None,
        icon="fa-file-excel-o",
        multiple=False,
        single=True)
    def download_raw_metadata_csv(self, item):
        output = BytesIO()
        tag = 'Empty'
        if isinstance(item.formatted_csv_data, str) and \
           len(item.formatted_csv_data.split("\n")) > 0:
            cvsStringIO = StringIO(item.formatted_csv_data)
            df = pd.read_csv(cvsStringIO, header=0)
            df.to_csv(output, index=False)
            tag = item.metadata_tag
        else:
            df = pd.DataFrame([])
            df.to_csv(output, index=False)
        output.seek(0)
        self.update_redirect()
        return send_file(output, download_name=f"{tag}_formatted.csv", as_attachment=True)

    @action(
        "mark_raw_metadata_as_rejected",
        "Reject raw metadata",
        confirmation="Mark metadata as rejected ?",
        icon="fa-exclamation",
        multiple=False,
        single=True)
    def mark_raw_metadata_as_rejected(self, item):
        try:
            (db.session
             .query(RawMetadataModel)
             .filter(RawMetadataModel.raw_metadata_id==item.raw_metadata_id)
             .update({'status': 'REJECTED'}))
            db.session.commit()
            flash("Rejected metadata  {item.metadata_tag}", "info")
        except Exception as e:
            db.session.rollback()
            log.error(e)
        finally:
            self.update_redirect()
            return redirect(url_for('RawMetadataValidationView.list'))

    @action(
        "validate_raw_metadata",
        "Validate and submit metadata",
        confirmation="Run validation and trigger pipeline?",
        icon="fa-rocket",
        multiple=True, single=False)
    def validate_metadata(self, item):
        id_list = list()
        tag_list = list()
        if isinstance(item, list):
            id_list = [i.raw_metadata_id for i in item]
            tag_list = [i.metadata_tag for i in item]
        else:
            id_list = [item.raw_metadata_id]
            tag_list = [item.metadata_tag]
        try:
            _ = \
                async_validate_metadata\
                .apply_async(args=[id_list])
            flash(
                f"Submitted jobs for {', '.join(tag_list)}",
                "info")
        except Exception as e:
            log.error(e)
            flash(
                f"Failed to submit jobs for {', '.join(tag_list)}",
                "danger")
        self.update_redirect()
        return redirect(self.get_redirect())