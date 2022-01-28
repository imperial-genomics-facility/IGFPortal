import logging
import pandas as pd
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask import redirect, flash, url_for, send_file, abort
from flask_appbuilder import ModelView
from flask_appbuilder.baseviews import expose
from . import db, celery
from io import BytesIO
from flask_appbuilder.actions import action
from .samplesheet.samplesheet_util import SampleSheet
from .models import SampleSheetModel

class SampleSheetView(ModelView):
    datamodel = SQLAInterface(SampleSheetModel)

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
        self.update_redirect()
        return redirect(self.get_redirect())