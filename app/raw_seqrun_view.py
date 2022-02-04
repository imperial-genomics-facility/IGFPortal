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
        "raw_seqrun_igf_id": "Sequencing id",
        "status": "Status",
        "samplesheet.samplesheet_tag": "SampleSheet tag",
        "date_stamp": "Updated on"
    }
    list_columns = ["raw_seqrun_igf_id", "status", "samplesheet.samplesheet_tag", "date_stamp"]
    show_columns = ["raw_seqrun_igf_id", "status", "samplesheet.samplesheet_tag", "date_stamp"]
    edit_columns = ["raw_seqrun_igf_id", "samplesheet.samplesheet_tag"]
    base_permissions = ["can_list", "can_show", "can_edit"]
    base_order = ("raw_seqrun_igf_id", "desc")
    edit_form_extra_fields = {
        "samplesheet.samplesheet_tag": QuerySelectField(
            "SamplesheetModel",
            query_factory=samplesheet_query,
            widget=Select2Widget()
        )
    }

    @action("trigger_pre_demultiplexing", "Trigger pre_demultiplexing pipeline", confirmation="confirm pipeline run", icon="fa-rocket")
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

    @action("mark_raw_run_rejected", "Mark run as rejected", confirmation="Reject run?", icon="fa-ban")
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