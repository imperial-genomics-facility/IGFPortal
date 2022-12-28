import logging
from flask import abort
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect, has_access
from .models import Project_info_data
from flask_appbuilder.baseviews import BaseView, expose
from flask_appbuilder.security.decorators import protect, has_access
from . import db

log = logging.getLogger(__name__)

def fetch_project_info_data():
    try:
        results = \
            db.session.query(Project_info_data).\
            filter(Project_info_data.project_id==1).one_or_none()
        if results is None:
            abort(404)
        return results.sample_read_count_data
    except Exception as e:
        log.error(e)
