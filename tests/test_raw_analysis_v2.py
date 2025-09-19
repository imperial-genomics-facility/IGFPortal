from app.models import (
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2,
    RawProject,
    RawPipeline)
from app.raw_analysis_view_v2 import (
    RawAnalysisTemplateV2View,
    RawAnalysisSchemaV2View,
    action_validate_json_analysis_schema,
    async_validate_analysis_schema)
from app.raw_analysis.raw_analysis_util_v2 import (
    raw_project_query,
    raw_pipeline_query,
    validate_analysis_json_schema)
from unittest.mock import patch


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

def test_validate_analysis_json_schema(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="dag_test1",
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
    schema1 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=1,
          pipeline_id=pipeline1.pipeline_id,
          json_schema='{"A": "B"}')
    schema2 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=2,
          pipeline_id=pipeline2.pipeline_id,
          json_schema='{"A", "B"}')
    try:
        db.session.add(pipeline1)
        db.session.add(pipeline2)
        db.session.add(schema1)
        db.session.add(schema2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    status = \
        validate_analysis_json_schema(
            raw_analysis_schema_id=pipeline1.pipeline_id)
    assert status == 'VALIDATED'
    status = \
        validate_analysis_json_schema(
            raw_analysis_schema_id=pipeline2.pipeline_id)
    assert status == 'FAILED'


def test_async_validate_analysis_schema(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="dag_test1",
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
    schema1 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=1,
          pipeline_id=pipeline1.pipeline_id,
          json_schema='{"A": "B"}')
    schema2 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=2,
          pipeline_id=pipeline2.pipeline_id,
          json_schema='{"A", "B"}')
    try:
        db.session.add(pipeline1)
        db.session.add(pipeline2)
        db.session.add(schema1)
        db.session.add(schema2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    results = \
        async_validate_analysis_schema(
            id_list=[schema1.raw_analysis_schema_id])
    assert len(results) == 1
    assert schema1.raw_analysis_schema_id in results
    assert results.get(schema1.raw_analysis_schema_id) == 'VALIDATED'
    results = \
        async_validate_analysis_schema(
            id_list=[schema2.raw_analysis_schema_id])
    assert len(results) == 1
    assert schema2.raw_analysis_schema_id in results
    assert results.get(schema2.raw_analysis_schema_id) == 'FAILED'


def test_action_validate_json_analysis_schema(db):
    pipeline1 = \
        RawPipeline(
            pipeline_id=1,
            pipeline_name="dag_test1",
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
    schema1 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=1,
          pipeline_id=pipeline1.pipeline_id,
          json_schema='{"A": "B"}')
    schema2 = \
      RawAnalysisValidationSchemaV2(
          raw_analysis_schema_id=2,
          pipeline_id=pipeline2.pipeline_id,
          json_schema='{"A", "B"}')
    try:
        db.session.add(pipeline1)
        db.session.add(pipeline2)
        db.session.add(schema1)
        db.session.add(schema2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    print(db.session.query(RawAnalysisValidationSchemaV2).all())
    with patch("app.raw_analysis_view_v2.async_validate_analysis_schema", return_values=["AAA"]):
        pipeline_list, _ = \
            action_validate_json_analysis_schema(
                item=[schema1, schema2])
        assert len(pipeline_list) == 2
        assert pipeline1.pipeline_name in pipeline_list
        assert pipeline2.pipeline_name in pipeline_list
        pipeline_list, _ = \
            action_validate_json_analysis_schema(
                item=schema1)
        assert len(pipeline_list) == 1
        assert pipeline1.pipeline_name in pipeline_list
