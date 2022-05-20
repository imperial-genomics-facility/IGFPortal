from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from flask_appbuilder import ModelView
from .models import RawSeqrun, SampleSheetModel
import logging
from flask import redirect, flash
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from . import db
from .raw_seqrun.raw_seqrun_util import check_and_filter_raw_seqruns_after_checking_samplesheet
from .raw_seqrun.raw_seqrun_util import change_raw_run_status

def samplesheet_query():
    results = \
        db.session.\
            query(SampleSheetModel).\
            filter(SampleSheetModel.status=='PASS').\
            filter(SampleSheetModel.validation_time >= SampleSheetModel.update_time).\
            order_by(SampleSheetModel.samplesheet_id.desc()).\
            limit(20).\
            all()
    return results

class RawSeqrunView(ModelView):
    datamodel = SQLAInterface(RawSeqrun)
    label_columns = {
        "raw_seqrun_igf_id": "Sequencing Id",
        "status": "Status",
        "samplesheet": "SampleSheet tag",
        "date_stamp": "Updated on"
    }
    list_columns = [
        "raw_seqrun_igf_id",
        "status",
        "samplesheet.samplesheet_tag",
        "samplesheet.status",
        "override_cycles",
        "date_stamp"]
    show_columns = [
        "raw_seqrun_igf_id",
        "status",
        "override_cycles",
        "date_stamp",
        "samplesheet.samplesheet_tag",
        "samplesheet.status",
        "samplesheet.csv_data"]
    label_columns = {
        "raw_seqrun_igf_id": "Raw seqrun igf id",
        "status": "Status",
        "samplesheet.samplesheet_tag": "Samplesheet tag",
        "samplesheet.status": "Samplesheet status",
        "samplesheet.csv_data": "Samplesheet csv data",
        "override_cycles": "Override cycles",
        "date_stamp": "Run date"}
    edit_columns = ["raw_seqrun_igf_id", "samplesheet", "override_cycles"]
    base_permissions = ["can_list", "can_show", "can_edit"]
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

    @action("get_new_seqrun", "Get new seqrun", confirmation="Are you sure?" , icon="fa-paper-plane-o", multiple=False)
    def get_new_seqrun(self, ids):
        flash("New seqrun(s) added to queue")
        self.update_redirect()
        return redirect(self.get_redirect())

    """
    @action("mark_raw_run_rejected", "Reject run", confirmation="Reject run?", icon="fa-ban", multiple=False)
    def mark_raw_run_rejected(self, item):
        run_list = list()
        if isinstance(item, list):
            run_list = [i.raw_seqrun_igf_id for i in item]
        else:
            run_list = [item.raw_seqrun_igf_id]
        try:
            change_raw_run_status(
                run_list=run_list,
                status='REJECTED')
        except Exception as e:
            logging.error(e)
        self.update_redirect()
        return redirect(self.get_redirect())
    """

    @action("first_run_demultiplexing", "Run pipeline", confirmation="Confirm pipeline run?", multiple=False, icon="fa-space-shuttle")
    def firts_run_demultiplexing(self, item):
        run_list = list()
        if isinstance(item, list):
            run_list = [i.raw_seqrun_igf_id for i in item]
        else:
            run_list = [item.raw_seqrun_igf_id]
        flash("Submitted jobs for {0}".format(', '.join(run_list)), "info")
        self.update_redirect()
        return redirect(self.get_redirect())


    @action("rerun_demultiplexing", "Re-run pipeline", confirmation="All fastq files will be replaced. Confirm pipeline run?", multiple=False, icon="fa-plane")
    def rerun_demultiplexing(self, item):
        run_list = list()
        if isinstance(item, list):
            run_list = [i.raw_seqrun_igf_id for i in item]
        else:
            run_list = [item.raw_seqrun_igf_id]
        flash("Submitted jobs for {0}".format(', '.join(run_list)), "info")
        self.update_redirect()
        return redirect(self.get_redirect())


    @action("trigger_pre_demultiplexing", "Test barcodes", confirmation="confirm pipeline run", icon="fa-rocket")
    def trigger_pre_demultiplexing(self, item):
        run_list = list()
        if isinstance(item, list):
            run_list = [i.raw_seqrun_igf_id for i in item]
        else:
            run_list = [item.raw_seqrun_igf_id]
        id_list, run_list = \
            check_and_filter_raw_seqruns_after_checking_samplesheet(
                raw_seqrun_igf_ids=run_list)
        flash("Submitted jobs for {0}".format(', '.join(run_list)), "info")
        self.update_redirect()
        return redirect(self.get_redirect())
