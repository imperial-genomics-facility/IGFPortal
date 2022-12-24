import logging, tempfile, os
from io import BytesIO
from .models import RawAnalysis, RawMetadataModel
from flask_appbuilder import ModelView
from flask_appbuilder.models.sqla.filters import FilterInFunction
from flask import redirect, flash, send_file
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from . import db
from . import celery
from .raw_analysis.raw_analysis_util import validate_analysis_json

@celery.task(bind=True)
def async_validate_analysis_yaml(self, id_list):
    try:
        pass
    except Exception as e:
        logging.error(
            "Failed to run celery job, error: {0}".\
                    format(e))

class RawAnalysisView(ModelView):
    datamodel = SQLAInterface(RawAnalysis)
    list_columns = ["analysis_tag", "status", "date_stamp"]
    show_columns = ["analysis_tag", "analysis_yaml", "status", "report", "date_stamp"]
    add_columns = ["analysis_tag", "analysis_yaml"]
    edit_columns = ["analysis_tag", "analysis_yaml"]
    base_filters = [
        ["status", FilterInFunction, lambda: ["UNKNOWN", "FAILED"]]]
    base_order = ("raw_analysis_id", "desc")

    @action("validate_and_submit_analysis", "Validate and upload analysis", confirmation="Validate analysis design?", icon="fa-rocket")
    def validate_and_submit_analysis(self, item):
        analysis_list = list()
        id_list = list()
        if isinstance(item, list):
            analysis_list = [i.analysis_tag for i in item]
            id_list = [i.raw_analysis_id for i in item]
        else:
            analysis_list = [item.analysis_tag]
            id_list = [item.raw_analysis_id]
        flash("Submitted jobs for {0}".format(', '.join(analysis_list)), "info")
        self.update_redirect()
        return redirect(self.get_redirect())


    @action("download_raw_analysis_damp", "Download analysis yaml", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def download_raw_analysis_damp(self, item):
        output = BytesIO(item.analysis_yaml.encode('utf-8'))
        analysis_tag = item.analysis_tag.encode('utf-8').decode()
        output.seek(0)
        self.update_redirect()
        return send_file(output, attachment_filename='{0}_analysis.yaml'.format(analysis_tag), as_attachment=True)