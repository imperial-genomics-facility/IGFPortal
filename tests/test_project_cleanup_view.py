import os
import requests
from unittest.mock import MagicMock
from app.models import ProjectCleanup
from unittest.mock import patch
from datetime import datetime, timedelta
from app.project_cleanup_view import async_trigger_airflow_cleanup_pipeline

@patch(
    'app.project_cleanup_view.trigger_airflow_pipeline',
    return_value=requests.patch('https://httpbin.org/patch',
    data ={'key': 'value'},
    headers={'Content-Type': 'application/json'}))
def test_async_trigger_airflow_cleanup_pipeline(mock_object, db, tmp_path):
    project_cleanup1 = \
        ProjectCleanup(
            user_email='e@g.com',
            user_name='e g',
            projects='["ProjectA", "ProjectB"]',
            deletion_date=datetime.now()+timedelta(days=15),
            status='NOT_STARTED',
            update_date=datetime.now(),
            created_by_fk=1,
            changed_by_fk=1)
    project_cleanup2 = \
        ProjectCleanup(
            user_email='f@h.com',
            user_name='f h',
            projects='["ProjectC", "ProjectD"]',
            deletion_date=datetime.now()+timedelta(days=15),
            status='NOT_STARTED',
            update_date=datetime.now(),
            created_by_fk=1,
            changed_by_fk=1)
    try:
        db.session.add(project_cleanup1)
        db.session.add(project_cleanup2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    p = tmp_path / "airflow.json"
    os.environ['AIRFLOW_CONF_FILE'] = str(p)
    p.write_text('{"url": "url", "username":"username", "password":"password", "test_dag": "test_dag"}')
    result = async_trigger_airflow_cleanup_pipeline('test_dag', [{'project_cleanup_id': project_cleanup1.project_cleanup_id}])
    assert project_cleanup1.project_cleanup_id in result