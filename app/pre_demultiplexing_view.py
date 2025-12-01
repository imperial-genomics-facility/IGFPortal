import logging
from typing import Any
from io import BytesIO
from app import cache
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView
from flask_appbuilder.baseviews import expose
from flask import redirect, flash, url_for, send_file
from flask_appbuilder.security.decorators import has_access
from . import db
from .models import PreDeMultiplexingData

log = logging.getLogger(__name__)

"""
    Pre de-multiplexing view
"""

class PreDeMultiplexingDataView(ModelView):
    datamodel = SQLAInterface(PreDeMultiplexingData)
    label_columns = {
        'run_name':'Sequencing run',
        'samplesheet_tag':'Tag',
        'date_stamp': 'Updated on',
        'report': 'Report',
        'download_report': 'Download'}
    list_columns = [
        'run_name',
        'samplesheet_tag',
        'date_stamp',
        'report',
        'download_report']
    base_permissions = ['can_list', 'can_download_reports']#, 'can_get_report']
    base_order = ("date_stamp", "desc")

    @expose("/download/rawdata/<int:record_id>")
    @has_access
    @cache.cached(timeout=600)
    def download_reports(self, record_id: str) -> Any:
        try:
            records = (
                db.session
                .query(
                    PreDeMultiplexingData.samplesheet_tag,
                    PreDeMultiplexingData.file_path)
                .filter(PreDeMultiplexingData.demult_id==record_id)
                .one_or_none()
            )
            if records is None:
                raise ValueError(
                    f"Report not found for id: {record_id}"
                )
            (sample_sheet_tag, file_path) = records
            with open(file_path, 'rb') as fp:
                html_data = fp.read()
            output = BytesIO(html_data)
            sample_sheet_tag = (
                sample_sheet_tag
                .encode('utf-8')
                .decode()
            )
            output.seek(0)
            self.update_redirect()
            return send_file(
                output,
                download_name=f'{sample_sheet_tag}.html',
                as_attachment=True
            )
        except Exception as e:
            log.error(e)
            flash('Failed to download report', 'danger')
            return redirect(url_for('PreDeMultiplexingDataView.list'))