import logging
from flask import url_for
from app import cache
from flask_appbuilder.baseviews import BaseView, expose
from flask_appbuilder.security.decorators import has_access
from app import db
from .models import (
    PreDeMultiplexingData,
    IlluminaInteropData)

log = logging.getLogger(__name__)

def get_path_for_predemult_report(
    record_id: int
    ) -> str:
    try:
        record = (
            db.session
            .query(PreDeMultiplexingData.file_path)
            .filter(PreDeMultiplexingData.demult_id==record_id)
            .one_or_none()
        )
        if record is None:
            log.warning(
                f"Missing pre-demult data for id {record_id}")
            return ''
        (file_path,) = \
            record
        return file_path
    except Exception as e:
        raise ValueError(
            f"Failed to get report for predemult entry {record_id},"
            + f"error: {e}"
        )

def get_path_for_interop_report(
    record_id: int
    ) -> str:
    try:
        record = (
            db.session
            .query(IlluminaInteropData.file_path)
            .filter(IlluminaInteropData.report_id==record_id)
            .one_or_none()
        )
        if record is None:
            log.warning(
                f"Missing Interop data for id {record_id}")
            return ''
        (file_path,) = \
            record
        return file_path
    except Exception as e:
        raise ValueError(
            f"Failed to get report for interop report entry {record_id},"
            + f" error: {e}"
        )

class IFrameView(BaseView):
    route_base = "/"

    @expose("/static/predemult/<int:record_id>")
    @has_access
    @cache.cached(timeout=1200)
    def view_predemult_report(self, record_id):
        file_path = get_path_for_predemult_report(
            record_id=record_id
        )
        url_link = url_for(
            'PreDeMultiplexingDataView.list'
        )
        if file_path.endswith('.html'):
            with open(file_path, 'r') as fp:
                html_data = fp.read()
            return self.render_template(
                "iframe.html",
                html_data=html_data,
                url_link=url_link
            )
        else:
            return self.response(500)

    @expose("/static/interop/<int:record_id>")
    @has_access
    @cache.cached(timeout=1200)
    def view_interop_report(self, record_id):
        file_path = get_path_for_interop_report(
            record_id=record_id
        )
        url_link = url_for(
            'IlluminaInteropDataView.list'
        )
        if file_path.endswith('.html'):
            with open(file_path, 'r') as fp:
                html_data = fp.read()
            return self.render_template(
                "iframe.html",
                html_data=html_data,
                url_link=url_link)
        else:
            return self.response(500)
