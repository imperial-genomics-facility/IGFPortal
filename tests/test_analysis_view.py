import os
import requests
from app.models import Analysis
from app.models import Pipeline_seed
from app.models import Pipeline
from app.models import Project
from unittest.mock import patch
from app.analysis_view import get_analysis_pipeline_seed_status
from app.analysis_view import async_submit_analysis_pipeline

def test_get_analysis_pipeline_seed_status(db):
    project1 = \
        Project(
            project_igf_id='project1')
    pipeline1 = \
        Pipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    pipeline2 = \
        Pipeline(
            pipeline_name='pipeline2',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    analysis1 = \
        Analysis(
            project=project1,
            analysis_name='analysis1',
            analysis_type='pipeline1',
            analysis_description='test'
        )
    analysis2 = \
        Analysis(
            project=project1,
            analysis_name='analysis2',
            analysis_type='pipeline1',
            analysis_description='test'
        )
    analysis3 = \
        Analysis(
            project=project1,
            analysis_name='analysis3',
            analysis_type='pipeline2',
            analysis_description='test'
        )
    try:
        db.session.add(project1)
        db.session.add(pipeline1)
        db.session.add(pipeline2)
        db.session.add(analysis1)
        db.session.add(analysis2)
        db.session.add(analysis3)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    pipeline_seed1 = \
        Pipeline_seed(
            seed_id=analysis1.analysis_id,
            seed_table='analysis',
            pipeline=pipeline1,
            status='SEEDED'
        )
    pipeline_seed2 = \
        Pipeline_seed(
            seed_id=analysis2.analysis_id,
            seed_table='analysis',
            pipeline=pipeline1,
            status='FINISHED'
        )
    try:
        db.session.add(pipeline_seed1)
        db.session.add(pipeline_seed2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    assert pipeline_seed1.seed_id != pipeline_seed2.seed_id
    assert pipeline_seed2.status == 'FINISHED'
    status1 = \
        get_analysis_pipeline_seed_status(
            analysis_id=analysis1.analysis_id)
    assert status1 == 'VALID'
    status2 = \
        get_analysis_pipeline_seed_status(
            analysis_id=analysis2.analysis_id)
    assert status2 == 'INVALID'
    status3 = \
        get_analysis_pipeline_seed_status(
            analysis_id=analysis2.analysis_id)
    assert status3 == 'INVALID'

@patch('app.analysis_view.trigger_airflow_pipeline', return_value=requests.patch('https://httpbin.org/patch', data ={'key': 'value'}, headers={'Content-Type': 'application/json'}))
def test_async_submit_analysis_pipeline(mock_object, db):
    project1 = \
        Project(
            project_igf_id='project1')
    pipeline1 = \
        Pipeline(
            pipeline_name='pipeline1',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    pipeline2 = \
        Pipeline(
            pipeline_name='pipeline2',
            pipeline_db='test',
            pipeline_type='AIRFLOW')
    analysis1 = \
        Analysis(
            project=project1,
            analysis_name='analysis1',
            analysis_type='pipeline1',
            analysis_description='test'
        )
    analysis2 = \
        Analysis(
            project=project1,
            analysis_name='analysis2',
            analysis_type='pipeline1',
            analysis_description='test'
        )
    analysis3 = \
        Analysis(
            project=project1,
            analysis_name='analysis3',
            analysis_type='pipeline2',
            analysis_description='test'
        )
    try:
        db.session.add(project1)
        db.session.add(pipeline1)
        db.session.add(pipeline2)
        db.session.add(analysis1)
        db.session.add(analysis2)
        db.session.add(analysis3)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    pipeline_seed1 = \
        Pipeline_seed(
            seed_id=analysis1.analysis_id,
            seed_table='analysis',
            pipeline=pipeline1,
            status='SEEDED'
        )
    pipeline_seed2 = \
        Pipeline_seed(
            seed_id=analysis2.analysis_id,
            seed_table='analysis',
            pipeline=pipeline1,
            status='FINISHED'
        )
    try:
        db.session.add(pipeline_seed1)
        db.session.add(pipeline_seed2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    os.environ['AIRFLOW_CONF_FILE'] = '/tmp/'
    result = async_submit_analysis_pipeline([analysis1.analysis_id])
    assert analysis1.analysis_id in result
