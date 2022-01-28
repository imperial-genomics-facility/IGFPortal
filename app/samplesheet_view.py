import logging
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import redirect, flash, url_for, send_file, abort
from flask_appbuilder import ModelView
from flask_appbuilder.baseviews import expose
from . import celery
from io import BytesIO
from flask_appbuilder.actions import action
from .models import SampleSheetModel
from .samplesheet.samplesheet_util import validate_samplesheet_data_and_update_db


@celery.task(bind=True)
def async_validate_samplesheet(self, tag_list):
    try:
        for samplesheet_tag in tag_list:
            validate_samplesheet_data_and_update_db(
                samplesheet_tag=samplesheet_tag)
        return {}
    except Exception as e:
        logging.error(
            "Failed to run celery job, error: {0}".\
                    format(e))


class SampleSheetView(ModelView):
    datamodel = SQLAInterface(SampleSheetModel)
    label_columns = {
        'samplesheet_tag':'Tag',
        'csv_data': 'CSV',
        'status': 'Status',
        'report': 'Report',
        'validation_time': 'Validated on',
        'date_stamp': 'Updated on'}
    list_columns = [
        "samplesheet_tag",
        "status",
        "update_time",
        "validation_time"]
    add_columns = [
        "samplesheet_tag",
        "csv_data"]
    edit_columns = [
        "samplesheet_tag",
        "csv_data"]
    base_order = ("samplesheet_id", "desc")

    @action("download_samplesheet", "Download samplesheet", confirmation=None, icon="fa-excel", multiple=False, single=True)
    def download_samplesheet(self, item):
        output = BytesIO(item.csv_data.encode())
        samplesheet_tag = item.samplesheet_tag.decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, attachment_filename='SampleSheet_{0}.csv'.format(samplesheet_tag), as_attachment=True)


    @action("validate_samplesheet", "Validate SampleSheets", confirmation="Run validation?", icon="fa-rocket")
    def validate_samplesheet(self, item):
        data = list()
        if isinstance(item, list):
            data = [i.samplesheet_tag for i in item]
        else:
            data = [item.samplesheet_tag]
        _ = \
            async_validate_samplesheet.\
                apply_async(args=[data])
        self.update_redirect()
        return redirect(self.get_redirect())