from app.models import (
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2,
    RawProject,
    RawPipeline)
from app.raw_analysis_view_v2 import (
    RawAnalysisTemplateV2View,
    RawAnalysisSchemaV2View)
from app.raw_analysis.raw_analysis_util_v2 import (
    raw_project_query,
    raw_pipeline_query)


def test_analysis_template_v2(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="test1",
            pipeline_db="test",
            pipeline_type="AIRFLOW")
    template1 = \
        RawAnalysisTemplateV2(
            template_id=1,
            pipeline_id=pipeline1.pipeline_id,
            template_data='{"A", "B"}')
    try:
        db.session.add(pipeline1)
        db.session.flush()
        db.session.add(template1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    template = db.session.query(RawAnalysisTemplateV2).filter(RawAnalysisTemplateV2.template_id==1).one_or_none()
    assert template is not None
    assert template.pipeline_id == 1


def test_raw_pipeline_query(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="test1",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    pipeline2 = \
        RawPipeline(
            pipeline_id=2,
            pipeline_name="dag_test2",
            pipeline_db="test",
            is_active="Y",
            pipeline_type="AIRFLOW")
    try:
        db.session.add(pipeline1)
        db.session.flush()
        db.session.add(pipeline2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    records = raw_pipeline_query()
    assert records is not None
    assert len(records) == 1
    pipeline_ids = [entry.pipeline_id for entry in records]
    assert 1 not in pipeline_ids
    assert 2 in pipeline_ids


def test_raw_project_query(db):
    project1 = \
        RawProject(
            project_id=1,
            project_igf_id="test1",
            deliverable="FASTQ")
    project2 = \
        RawProject(
            project_id=2,
            project_igf_id="test2",
            deliverable="COSMX")
    project3 = \
        RawProject(
            project_id=3,
            project_igf_id="test3",
            status="WITHDRAWN",
            deliverable="FASTQ")
    try:
        db.session.add(project1)
        db.session.add(project2)
        db.session.add(project3)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    records = raw_project_query()
    assert records is not None
    assert len(records) == 2
    project_ids = [entry.project_id for entry in records]
    assert 3 not in project_ids
    assert 2 in project_ids