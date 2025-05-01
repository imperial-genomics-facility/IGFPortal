import logging
import pandas as pd
from flask_babel import lazy_gettext
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.models.sqla.filters import FilterInFunction
from flask import redirect, flash, url_for, send_file, abort
from flask_appbuilder import ModelView
from flask_appbuilder.baseviews import expose
from . import celery
from io import BytesIO, StringIO
from flask_appbuilder.actions import action
from .models import RawCosMxMetadataModel
from . import db

@celery.task(bind=True)
def async_validate_metadata(self, id_list):
    try:
        results = list()
        for raw_cosmx_metadata_id in id_list:
            msg = \
                validate_raw_cosmx_metadata_and_set_db_status(
                    raw_cosmx_metadata_id=raw_cosmx_metadata_id)
            results.append(msg)
        return dict(zip(id_list, results))
    except Exception as e:
        logging.error(
            f"Failed to run celery job for metadata validation, error: {e}")

class RawCosmxMetadataSubmitView(ModelView):
    datamodel = SQLAInterface(RawCosMxMetadataModel)
    label_columns = {
        "cosmx_metadata_tag": "Tag",
        "formatted_csv_data": "CSV",
        "report": "Report",
        "status": "Status",
        "update_time": "Updated on"}
    list_columns = [
        "cosmx_metadata_tag",
        "status",
        "update_time"]
    show_columns = [
        "cosmx_metadata_tag",
        "formatted_csv_data",
        "report",
        "status",
        "update_time"]
    base_permissions = ["can_list", "can_show"]
    base_order = ("raw_cosmx_metadata_id", "desc")
    base_filters = [
        ["status", FilterInFunction, lambda: ["READY", "VALIDATED"]]]

    @action("upload_raw_metadata", "Mark for upload", confirmation="Change metadata status?", icon="fa-rocket")
    def upload_raw_metadata_csv(self, item):
        id_list = list()
        tag_list = list()
        if isinstance(item, list):
            id_list = [i.raw_cosmx_metadata_id for i in item]
            tag_list = [i.cosmx_metadata_tag for i in item]
        else:
            id_list = [item.raw_cosmx_metadata_id]
            tag_list = [item.cosmx_metadata_tag]
        try:
            mark_raw_cosmx_metadata_as_ready(id_list=id_list)
            flash(f"Marked metadata ready for {', '.join(tag_list)}", "info")
        except Exception as e:
            logging.error(e)
            flash(f"Error in upload {', '.join(tag_list)}", "danger")
        self.update_redirect()
        return redirect(self.get_redirect())

    @action("validate_raw_metadata", "Validate metadata", confirmation="Run validation?", icon="fa-rocket", multiple=True, single=False)
    def validate_metadata(self, item):
        id_list = list()
        tag_list = list()
        if isinstance(item, list):
            id_list = [i.raw_cosmx_metadata_id for i in item]
            tag_list = [i.cosmx_metadata_tag for i in item]
        else:
            id_list = [item.raw_cosmx_metadata_id]
            tag_list = [item.cosmx_metadata_tag]
        _ = \
            async_validate_metadata.\
                apply_async(args=[id_list])
        flash(f"Submitted jobs for {', '.join(tag_list)}", "info")
        self.update_redirect()
        return redirect(self.get_redirect())

    @action("mark_raw_metadata_as_rejected", "Reject raw metadata", confirmation="Mark metadata as rejected ?", icon="fa-exclamation", multiple=False, single=True)
    def mark_raw_metadata_as_rejected(self, item):
        try:
            db.session.\
                query(RawCosMxMetadataModel).\
                filter(RawCosMxMetadataModel.raw_cosmx_metadata_id==item.raw_cosmx_metadata_id).\
                update({'status': 'REJECTED'})
            db.session.commit()
            flash("Rejected metadata  {item.cosmx_metadata_tag}", "info")
        except Exception as e:
            db.session.rollback()
            logging.error(e)
        finally:
            self.update_redirect()
            return redirect(url_for('RawCosmxMetadataSubmitView.list'))