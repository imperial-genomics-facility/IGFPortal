from app.models import (
    RawAnalysisTemplateV2,
    RawAnalysisValidationSchemaV2,
    RawAnalysisV2,
    RawPipeline)

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
