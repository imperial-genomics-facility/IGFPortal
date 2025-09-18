from app import db
import logging
from app.models import (
    RawPipeline,
    RawProject,
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2)\

log = logging.getLogger(__name__)

def raw_project_query():
    try:
        results = \
            db.session.\
                query(RawProject).\
                filter(RawProject.status=='ACTIVE').\
                order_by(RawProject.project_id.desc()).\
                limit(100).\
                all()
        return results
    except Exception as e:
        raise ValueError(
            f"Failed to get project list, error: {e}")


def raw_pipeline_query():
    try:
        results = \
            db.session.\
                query(RawPipeline).\
                filter(RawPipeline.is_active=='Y').\
                filter(RawPipeline.pipeline_type=='AIRFLOW').\
                filter(RawPipeline.pipeline_name.like("dag%")).\
                order_by(RawPipeline.pipeline_id.desc()).\
                limit(100).\
                all()
        return results
    except Exception as e:
        raise ValueError(
            f"Failed to get pipeline list, error: {e}")