from wtforms.ext.sqlalchemy.fields import QuerySelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from flask_appbuilder import ModelView
from .models import RawSeqrun, SampleSheetModel
import logging
from flask_appbuilder.models.sqla.interface import SQLAInterface
from . import db

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
        "samplesheet": "SampleSheet tag",
        "date_stamp": "Updated on"
    }
    list_columns = ["raw_seqrun_igf_id", "status", "samplesheet", "date_stamp"]
    show_columns = ["raw_seqrun_igf_id", "status", "samplesheet", "date_stamp"]
    add_columns = ["raw_seqrun_igf_id", "status", "samplesheet"]
    edit_columns = ["raw_seqrun_igf_id", "status", "samplesheet"]
    base_permissions = ["can_list", "can_show", "can_add", "can_edit"]
    base_order = ("raw_seqrun_igf_id", "desc")
    add_form_extra_fields = {
        "samplesheet": QuerySelectField(
            "SamplesheetModel",
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
