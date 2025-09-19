from app import db
import json
import logging
from app.models import (
    RawPipeline,
    RawProject,
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2)

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


def validate_analysis_json_schema(
    raw_analysis_schema_id: int,
    validated_tag: str = 'VALIDATED',
    failed_tag: str = 'FAILED') -> str:
    try:
        status = failed_tag
        raw_analysis_schema = \
            db.session.\
                query(RawAnalysisValidationSchemaV2).\
                filter(RawAnalysisValidationSchemaV2.\
                       raw_analysis_schema_id==raw_analysis_schema_id).\
                one_or_none()
        if raw_analysis_schema is None:
            raise ValueError(
                f"No metadata entry found for id {raw_analysis_schema_id}")
        json_schema = \
            raw_analysis_schema.json_schema
        if json_schema is not None:
            try:
                _ = json.loads(json_schema)
                status = validated_tag
            except Exception as e:
                log.error(f"Failed to run json validation, error: {e}")
                status = failed_tag
        ## update db status
        try:
            db.session.\
                query(RawAnalysisValidationSchemaV2).\
                filter(RawAnalysisValidationSchemaV2.\
                       raw_analysis_schema_id==raw_analysis_schema_id).\
                update({'status': status})
            db.session.commit()
        except:
            db.session.rollback()
            raise
        return status
    except Exception as e:
        raise ValueError(
            f"Failed to validate json schema, error: {e}")