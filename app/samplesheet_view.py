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
def async_validate_samplesheet(self, id_list):
    try:
        results = list()
        for samplesheet_id in id_list:
            msg = \
                validate_samplesheet_data_and_update_db(
                    samplesheet_id=samplesheet_id)
            results.append(msg)
        return dict(zip(id_list, results))
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

    @action("download_samplesheet", "Download samplesheet", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def download_samplesheet(self, item):
        output = BytesIO(item.csv_data.encode())
        samplesheet_tag = item.samplesheet_tag.decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, attachment_filename='SampleSheet_{0}.csv'.format(samplesheet_tag), as_attachment=True)


    @action("validate_samplesheet", "Validate SampleSheets", confirmation="Run validation?", icon="fa-rocket")
    def validate_samplesheet(self, item):
        id_list = list()
        tag_list = list()
        if isinstance(item, list):
            id_list = [i.samplesheet_id for i in item]
            tag_list = [i.samplesheet_tag for i in item]
        else:
            id_list = [item.samplesheet_id]
            tag_list = [item.samplesheet_tag]
        _ = \
            async_validate_samplesheet.\
                apply_async(args=[id_list])
        flash("Submitted jobs for {0}".format(', '.join(tag_list)))
        self.update_redirect()
        return redirect(self.get_redirect())