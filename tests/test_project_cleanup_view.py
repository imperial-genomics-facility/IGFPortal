import os
import time
import requests
from unittest.mock import MagicMock
from app.models import ProjectCleanup
from unittest.mock import patch
from datetime import datetime, timedelta
from app.project_cleanup_view import (
    async_trigger_airflow_cleanup_pipeline,
    update_status_for_project_cleanup,
    parse_and_add_project_cleanup_data,
    update_trigger_date_for_cleanup)

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
    result = async_trigger_airflow_cleanup_pipeline('test_dag', [{'project_cleanup_id': project_cleanup1.project_cleanup_id}], 1)
    assert project_cleanup1.project_cleanup_id in result

def test_update_status_for_project_cleanup(db):
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
    update_status_for_project_cleanup(
        project_cleanup_id_list=[project_cleanup1.project_cleanup_id],
        status='PROCESSING',
        user_id=1)
    pc1 = \
        db.session.\
            query(ProjectCleanup).\
            filter(ProjectCleanup.project_cleanup_id==project_cleanup1.project_cleanup_id).\
            one_or_none()
    assert pc1.status == 'PROCESSING'
    pc2 = \
        db.session.\
            query(ProjectCleanup).\
            filter(ProjectCleanup.project_cleanup_id==project_cleanup2.project_cleanup_id).\
            one_or_none()
    assert pc2.status == 'NOT_STARTED'


def test_update_trigger_date_for_cleanup(db):
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
    try:
        db.session.add(project_cleanup1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    update_time1 = str(project_cleanup1.update_date)
    time.sleep(2)
    update_trigger_date_for_cleanup(
        project_cleanup_id=project_cleanup1.project_cleanup_id,
        user_id=1)
    pc1 = \
        db.session.\
            query(ProjectCleanup).\
            filter(ProjectCleanup.project_cleanup_id==project_cleanup1.project_cleanup_id).\
            one_or_none()
    assert update_time1 != str(pc1.update_date)

def test_parse_and_add_project_cleanup_data(db):
    pc1 = \
        db.session.\
            query(ProjectCleanup).\
            filter(ProjectCleanup.user_email=='a@b.com').\
            one_or_none()
    assert pc1 is None
    data = """[{
        "email_id": "a@b.com",
        "name": "A B",
        "projects": ["ProjectA", "ProjectB"]}, {
        "email_id": "c@e.com",
        "name": "C E",
        "projects": ["ProjectC", "ProjectE"]}]"""
    parse_and_add_project_cleanup_data(
        data=data,
        user_id=1)
    pc1 = \
        db.session.\
            query(ProjectCleanup).\
            filter(ProjectCleanup.user_email=='a@b.com').\
            one_or_none()
    assert pc1 is not None
    assert pc1.projects == "[\"ProjectA\", \"ProjectB\"]"
    pc2 = \
        db.session.\
            query(ProjectCleanup).\
            filter(ProjectCleanup.user_email=='c@e.com').\
            one_or_none()
    assert pc2 is not None
    assert pc2.projects == "[\"ProjectC\", \"ProjectE\"]"