import os
import time
import logging
from datetime import datetime
from wtforms_sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from flask_appbuilder import ModelView
from .models import RawSeqrun, SampleSheetModel
from flask import redirect, flash, url_for
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from . import db
from . import celery
from .airflow.airflow_api_utils import trigger_airflow_pipeline
from .airflow.airflow_api_utils import get_airflow_dag_id

log = logging.getLogger(__name__)

## TO DO: load DAG names from config file
TEST_BARCODE_DAG_TAG = 'de_multiplexing_test_barcode_dag'
PRODUCTION_PIPELINE_DAG_TAG = 'de_multiplexing_production_dag'
CLEAN_UP_DAG_TAG = 'de_multiplexing_cleanup_dag'

@celery.task(bind=True)
def async_trigger_airflow_pipeline(self, dag_id, run_list, update_trigger_date=False):
    try:
        results = list()
        run_id_list = list()
        for entry in run_list:
            run_id_list.\
                append(entry.get('seqrun_id'))
            res = \
                trigger_airflow_pipeline(
                    dag_id=dag_id,
                    conf_data=entry,
                    airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'])
            if res is not None and \
               update_trigger_date and \
               res.status_code == 200:
                update_trigger_date_for_seqrun(
                    seqrun_id=entry.get('seqrun_id'))
            time.sleep(10)
            results.append(res.status_code)
        return dict(zip(run_id_list, results))
    except Exception as e:
        raise ValueError(f"Failed to run celery job, error: {e}")


def update_trigger_date_for_seqrun(seqrun_id: int) -> None:
    try:
        trigger_time = datetime.now()
        try:
            db.session.\
                query(RawSeqrun).\
                filter(RawSeqrun.raw_seqrun_igf_id==seqrun_id).\
                update({"trigger_time": trigger_time})
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
        raise ValueError(f"Failed to ad trigger date, error: {e}")


def samplesheet_query():
    try:
        results = \
            db.session.\
                query(SampleSheetModel).\
                order_by(SampleSheetModel.samplesheet_id.desc()).\
                limit(100).\
                all()
        return results
    except Exception as e:
        raise ValueError(f"Failed to get samplesheet list, error: {e}")


class RawSeqrunView(ModelView):
    datamodel = SQLAInterface(RawSeqrun)
    list_columns = [
        "raw_seqrun_igf_id",
        "status",
        "samplesheet.samplesheet_tag",
        "samplesheet.status",
        "samplesheet.validation_time",
        "samplesheet.update_time",
        "override_cycles",
        "mismatches",
        "date_stamp",
        "trigger_time"]
    show_columns = [
        "raw_seqrun_igf_id",
        "status",
        "override_cycles",
        "mismatches",
        "date_stamp",
        "trigger_time",
        "samplesheet.samplesheet_id",
        "samplesheet.samplesheet_tag",
        "samplesheet.status",
        "samplesheet.validation_time",
        "samplesheet.update_time",
        "samplesheet.csv_data"]
    label_columns = {
        "raw_seqrun_igf_id": "Sequencing Id",
        "status": "Status",
        "samplesheet.samplesheet_id": "Samplesheet ID",
        "samplesheet.samplesheet_tag": "Samplesheet tag",
        "samplesheet.status": "Status",
        "samplesheet.csv_data": "Samplesheet csv",
        "samplesheet.validation_time": "Validated on",
        "samplesheet.update_time": "Updated on",
        "override_cycles": "Override cycles",
        "mismatches": "Barcode mismatch",
        "date_stamp": "Run date",
        "trigger_time": "Trigger date"}
    edit_columns = [
        "raw_seqrun_igf_id",
        "samplesheet",
        "override_cycles",
        "mismatches"]
    base_permissions = [
        "can_list",
        "can_show",
        "can_edit"]
    base_order = ("raw_seqrun_igf_id", "desc")
    add_form_extra_fields = {
        "samplesheet": QuerySelectField(
            "SampleSheetModel",
            query_factory=samplesheet_query,
            widget=Select2Widget()
        )
    }
    edit_form_extra_fields = {
        "samplesheet": QuerySelectField(
            "SamplesheetModel",
            query_factory=samplesheet_query,
            widget=Select2Widget()
        )
    }


    @action("run_demultiplexing", "Run De-multiplexing", confirmation="Run de-multiplexing pipeline ?", multiple=False, icon="fa-plane")
    def run_demultiplexing(self, item):
        try:
            run_list = list()
            run_id_list = list()
            if isinstance(item, list):
                for i in item:
                    if i.samplesheet is None or \
                    i.samplesheet.status != 'PASS' or \
                    i.samplesheet.validation_time < i.samplesheet.update_time:
                        flash(f"Invalide Samplesheet for {i.raw_seqrun_igf_id}", "danger")
                    else:
                        run_id_list.\
                            append(i.raw_seqrun_igf_id)
                        run_list.\
                            append({
                                'seqrun_id': i.raw_seqrun_igf_id,
                                'samplesheet_tag': i.samplesheet.samplesheet_tag,
                                'override_cycles': i.override_cycles,
                                'mismatches': i.mismatches})
            else:
                if item.samplesheet is None or \
                item.samplesheet.status != 'PASS' or \
                item.samplesheet.validation_time < item.samplesheet.update_time:
                    flash(f"Invalide Samplesheet for {item.raw_seqrun_igf_id}", "danger")
                else:
                    run_list = [{
                        'seqrun_id': item.raw_seqrun_igf_id,
                        'samplesheet_tag': item.samplesheet.samplesheet_tag,
                        'override_cycles': item.override_cycles,
                        'mismatches': item.mismatches}]
                run_id_list = [item.raw_seqrun_igf_id]
            if len(run_list) > 0:
                airflow_dag_id = \
                    get_airflow_dag_id(
                        airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'],
                        dag_tag=PRODUCTION_PIPELINE_DAG_TAG)
                if airflow_dag_id is None:
                    raise ValueError(
                        f"Failed to get airflow dag id for {PRODUCTION_PIPELINE_DAG_TAG}")
                _ = \
                    async_trigger_airflow_pipeline.\
                        apply_async(args=[airflow_dag_id, run_list, True])
                flash("Running de-multiplexing for {0}".format(', '.join(run_id_list)), "info")
            self.update_redirect()
            return redirect(url_for('RawSeqrunView.list'))
        except Exception as e:
            log.error(e)
            flash(f"Failed to run de-multiplexing for {', '.join(run_id_list)}", "danger")
            return redirect(url_for('RawSeqrunView.list'))


    @action("trigger_pre_demultiplexing", "Test barcodes", confirmation="Confirm test pipeline run ?", multiple=True, single=False, icon="fa-rocket")
    def trigger_pre_demultiplexing(self, item):
        try:
            run_list = list()
            run_id_list = list()
            if isinstance(item, list):
                for i in item:
                    if i.samplesheet is None or \
                       i.samplesheet.status != 'PASS' or \
                       i.samplesheet.validation_time < i.samplesheet.update_time:
                        flash(f"Invalide Samplesheet for {i.raw_seqrun_igf_id}", "danger")
                    else:
                        run_id_list.\
                            append(i.raw_seqrun_igf_id)
                        run_list.\
                            append({
                                'seqrun_id': i.raw_seqrun_igf_id,
                                'samplesheet_tag': i.samplesheet.samplesheet_tag,
                                'override_cycles': i.override_cycles,
                                'mismatches': i.mismatches})
            else:
                if item.samplesheet is None or \
                   item.samplesheet.status != 'PASS' or \
                   item.samplesheet.validation_time < item.samplesheet.update_time:
                    flash(f"Invalide Samplesheet for {item.raw_seqrun_igf_id}", "danger")
                else:
                    run_list = [{
                        'seqrun_id': item.raw_seqrun_igf_id,
                        'samplesheet_tag': item.samplesheet.samplesheet_tag,
                        'override_cycles': item.override_cycles,
                        'mismatches': item.mismatches}]
                run_id_list = [item.raw_seqrun_igf_id]
            if len(run_list) > 0:
                airflow_dag_id = \
                    get_airflow_dag_id(
                        airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'],
                        dag_tag=TEST_BARCODE_DAG_TAG)
                if airflow_dag_id is None:
                    raise ValueError(
                        f"Failed to get airflow dag id for {TEST_BARCODE_DAG_TAG}")
                _ = \
                    async_trigger_airflow_pipeline.\
                        apply_async(args=[airflow_dag_id, run_list, True])
                flash("Running test for {0}".format(', '.join(run_id_list)), "info")
            self.update_redirect()
            return redirect(url_for('RawSeqrunView.list'))
        except Exception as e:
            log.error(e)
            flash("Failed to run test for {0}".format(', '.join(run_id_list)), "danger")


    @action("cleanup_demultiplexing", "Remove fastqs for re-run", confirmation="Delete fastqs for all projects before re-run  ?", multiple=False, icon="fa-exclamation")
    def cleanup_demultiplexing(self, item):
        try:
            run_list = list()
            run_id_list = list()
            if isinstance(item, list):
                for i in item:
                    if i.samplesheet is None or \
                       i.samplesheet.status != 'PASS' or \
                       i.samplesheet.validation_time < i.samplesheet.update_time:
                        flash(f"Invalide Samplesheet for {i.raw_seqrun_igf_id}", "danger")
                    else:
                        run_id_list.\
                            append(i.raw_seqrun_igf_id)
                        run_list.\
                            append({
                                'seqrun_id': i.raw_seqrun_igf_id,
                                'samplesheet_tag': i.samplesheet.samplesheet_tag,
                                'override_cycles': i.override_cycles})
            else:
                if item.samplesheet is None or \
                   item.samplesheet.status != 'PASS' or \
                   item.samplesheet.validation_time < item.samplesheet.update_time:
                    flash(f"Invalide Samplesheet for {item.raw_seqrun_igf_id}", "danger")
                else:
                    run_list = [{
                        'seqrun_id': item.raw_seqrun_igf_id,
                        'samplesheet_tag': item.samplesheet.samplesheet_tag,
                        'override_cycles': item.override_cycles}]
                run_id_list = [item.raw_seqrun_igf_id]
            if len(run_list) > 0:
                airflow_dag_id = \
                    get_airflow_dag_id(
                        airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'],
                        dag_tag=CLEAN_UP_DAG_TAG)
                if airflow_dag_id is None:
                    raise ValueError(
                        f"Failed to get airflow dag id for {CLEAN_UP_DAG_TAG}")
                _ = \
                    async_trigger_airflow_pipeline.\
                        apply_async(args=[airflow_dag_id, run_list])
                flash("Removing fastqs for {0}".format(', '.join(run_id_list)), "info")
            self.update_redirect()
            return redirect(url_for('RawSeqrunView.list'))
        except Exception as e:
            log.error(e)
            flash("failed to remove fastqs for {0}".format(', '.join(run_id_list)), "danger")