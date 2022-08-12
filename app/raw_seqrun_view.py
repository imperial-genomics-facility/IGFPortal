import os
import time
import logging
from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from flask_appbuilder import ModelView
from .models import RawSeqrun, SampleSheetModel
from flask import redirect, flash
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from . import db
from . import celery
from .airflow.airflow_api_utils import trigger_airflow_pipeline

log = logging.getLogger(__name__)

@celery.task(bind=True)
def async_trigger_airflow_pipeline(self, dag_id, run_list):
    try:
        results = list()
        for entry in run_list:
            res = \
                trigger_airflow_pipeline(
                    dag_id=dag_id,
                    conf_data=entry,
                    airflow_conf_file=os.environ['AIRFLOW_CONF_FILE'])
            time.sleep(10)
            results.append(res.status_code)
        return dict(zip(run_list, results))
    except Exception as e:
        log.error(f"Failed to run celery job, error: {e}")


def samplesheet_query():
    results = \
        db.session.\
            query(SampleSheetModel).\
            order_by(SampleSheetModel.samplesheet_id.desc()).\
            limit(40).\
            all()
    return results

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
        "date_stamp"]
    show_columns = [
        "raw_seqrun_igf_id",
        "status",
        "override_cycles",
        "date_stamp",
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
        "date_stamp": "Run date"}
    edit_columns = [
        "raw_seqrun_igf_id",
        "samplesheet",
        "override_cycles"]
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
            _ = \
            async_trigger_airflow_pipeline.\
                apply_async(args=['dag24_build_bclconvert_dynamic_dags', run_list])
            flash("Running de-multiplexing for {0}".format(', '.join(run_id_list)), "info")
        self.update_redirect()
        return redirect(self.get_redirect())


    @action("trigger_pre_demultiplexing", "Test barcodes", confirmation="Confirm test pipeline run ?", multiple=True, single=False, icon="fa-rocket")
    def trigger_pre_demultiplexing(self, item):
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
            _ = \
            async_trigger_airflow_pipeline.\
                apply_async(args=['dag23_test_bclconvert_demult', run_list])
            flash("Running test for {0}".format(', '.join(run_id_list)), "info")
        self.update_redirect()
        return redirect(self.get_redirect())


    @action("cleanup_demultiplexing", "Remove fastqs for re-run", confirmation="Delete fastqs for all projects before re-run  ?", multiple=False, icon="fa-exclamation")
    def cleanup_demultiplexing(self, item):
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
        #if len(run_list) > 0:
        #    _ = \
        #    async_trigger_airflow_pipeline.\
        #        apply_async(args=['TODO', run_list])
            flash("Removing fastqs for {0}".format(', '.join(run_id_list)), "info")
        self.update_redirect()
        return redirect(self.get_redirect())