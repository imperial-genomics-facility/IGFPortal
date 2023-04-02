import logging, tempfile, os
from app.samplesheet.samplesheet_util import SampleSheet
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
    base_permissions = [
        "can_list",
        "can_show",
        "can_add",
        "can_edit"]
    base_order = ("samplesheet_id", "desc")

    @action("download_samplesheet", "Download samplesheet", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def download_samplesheet(self, item):
        try:
            output = BytesIO(item.csv_data.encode())
            samplesheet_tag = item.samplesheet_tag.encode()
            if isinstance(samplesheet_tag, bytes):
                samplesheet_tag = samplesheet_tag.decode()
            output.seek(0)
            self.update_redirect()
            return send_file(output, download_name=f"SampleSheet_{samplesheet_tag}.csv", as_attachment=True)
        except:
            flash('Failed to download samplesheet', 'danger')
            return redirect(url_for('SampleSheetView.list'))

    @action("download_samplesheet_with_I5_rc", "Download samplesheet with I5 RC", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def download_samplesheet_with_I5_rc(self, item):
        try:
            if item.status != 'PASS':
                flash('Samplesheet is not validated', 'danger')
                raise
            csv_data = item.csv_data
            if isinstance(csv_data, bytes):
                csv_data = csv_data.decode()
            i5_rc_csv_data = ''
            with tempfile.TemporaryDirectory() as temp_dir:
                csv_file = os.path.join(temp_dir, 'SampleSheet.csv')
                with open(csv_file, 'w') as fp:
                    fp.write(csv_data)
                sa = SampleSheet(infile=csv_file)
                i5_rc_csv_data = \
                    sa.get_samplesheet_with_reverse_complement_index(index_field='index2')
            output = BytesIO(i5_rc_csv_data.encode())
            samplesheet_tag = item.samplesheet_tag.encode()
            if isinstance(samplesheet_tag, bytes):
                samplesheet_tag = samplesheet_tag.decode()
            output.seek(0)
            #self.update_redirect()
            return send_file(output, download_name=f"SampleSheet-I5_RC_{samplesheet_tag}.csv", as_attachment=True)
        except:
            flash('Failed to download I5 RC samplesheet', 'danger')
            return redirect(url_for('SampleSheetView.list'))


    @action("download_v2_samplesheet", "Download v2 samplesheet", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def download_v2_samplesheet(self, item):
        try:
            if item.status != 'PASS':
                flash('Samplesheet is not validated', 'danger')
                raise
            csv_data = item.csv_data
            if isinstance(csv_data, bytes):
                csv_data = csv_data.decode()
            with tempfile.TemporaryDirectory() as temp_dir:
                csv_file = os.path.join(temp_dir, 'SampleSheet.csv')
                with open(csv_file, 'w') as fp:
                    fp.write(csv_data)
                sa = SampleSheet(infile=csv_file)
                v2_csv_data = sa.get_v2_samplesheet_data()
            output = BytesIO(v2_csv_data.encode())
            samplesheet_tag = item.samplesheet_tag.encode()
            if isinstance(samplesheet_tag, bytes):
                samplesheet_tag = samplesheet_tag.decode()
            output.seek(0)
            self.update_redirect()
            return send_file(output, download_name=f"SampleSheet-V2_{samplesheet_tag}.csv", as_attachment=True)
        except:
            flash('Failed to download v2 samplesheet', 'danger')
            return redirect(url_for('SampleSheetView.list'))

    @action("validate_samplesheet", "Validate SampleSheets", confirmation="Run validation?", icon="fa-rocket", multiple=True, single=False)
    def validate_samplesheet(self, item):
        try:
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
            flash("Submitted jobs for {0}".format(', '.join(tag_list)), "info")
            self.update_redirect()
            return redirect(self.get_redirect())
        except:
            flash('Failed to validate samplesheet', 'danger')
            return redirect(url_for('SampleSheetView.list'))
