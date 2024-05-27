import json
import os
from io import BytesIO
from datetime import datetime, timedelta
from app.models import ProjectCleanup
from flask_appbuilder.const import (
    API_SECURITY_PASSWORD_KEY,
    API_SECURITY_PROVIDER_KEY,
    API_SECURITY_REFRESH_KEY,
    API_SECURITY_USERNAME_KEY)

def test_get_project_cleanup_data(db, test_client, tmp_path):
    res = \
        test_client.post(
            "/api/v1/security/login",
            json={
                API_SECURITY_USERNAME_KEY: "admin",
                API_SECURITY_PASSWORD_KEY: "password",
                API_SECURITY_PROVIDER_KEY: "db"})
    assert res.status_code == 200
    token = \
        json.loads(res.data.decode("utf-8")).\
            get("access_token")
    res = \
        test_client.post(
            '/api/v1/project_cleanup/get_project_cleanup_data/1',
            headers={"Authorization": f"Bearer {token}"})
    json_file = \
        os.path.join(tmp_path, 'project_cleanup_1.json')
    with open(json_file, 'wb') as fp:
        fp.write(res.data)
    with open(json_file, 'r') as fp:
        json_data = json.load(fp)
    assert 'user_email' in json_data
    assert 'user_name' in json_data
    assert 'projects' in json_data
    assert 'status' in json_data
    assert 'deletion_date' in json_data
    assert json_data.get('user_email') == ''
    assert json_data.get('user_name') == ''
    assert json_data.get('projects') == ''
    assert json_data.get('status') == ''
    assert json_data.get('deletion_date') == ''
    project_cleanup1 = \
        ProjectCleanup(
            user_email='e@g.com',
            user_name='e g',
            projects='["ProjectA", "ProjectB"]',
            deletion_date=datetime.now()+timedelta(days=15),
            created_by_fk=1,
            changed_by_fk=1)
    project_cleanup2 = \
        ProjectCleanup(
            user_email='f@h.com',
            user_name='f h',
            projects='["ProjectC", "ProjectD"]',
            deletion_date=datetime.now()+timedelta(days=15),
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
    res = \
        test_client.post(
            '/api/v1/project_cleanup/get_project_cleanup_data/1',
            headers={"Authorization": f"Bearer {token}"})
    json_file = \
        os.path.join(tmp_path, 'project_cleanup_1.json')
    with open(json_file, 'wb') as fp:
        fp.write(res.data)
    with open(json_file, 'r') as fp:
        json_data = json.load(fp)
    assert 'user_email' in json_data
    assert 'user_name' in json_data
    assert 'projects' in json_data
    assert 'status' in json_data
    assert 'deletion_date' in json_data
    assert json_data.get('user_email') == 'e@g.com'
    assert json_data.get('user_name') == 'e g'
    assert json_data.get('projects') == '["ProjectA", "ProjectB"]'
    assert json_data.get('status') == 'NOT_STARTED'

def test_mark_user_notified(db, test_client):
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
    res = \
        test_client.post(
            "/api/v1/security/login",
            json={
                API_SECURITY_USERNAME_KEY: "admin",
                API_SECURITY_PASSWORD_KEY: "password",
                API_SECURITY_PROVIDER_KEY: "db"})
    assert res.status_code == 200
    token = \
        json.loads(res.data.decode("utf-8")).\
            get("access_token")
    res = \
        test_client.post(
            f'/api/v1/project_cleanup/mark_user_notified/{project_cleanup1.project_cleanup_id}',
            headers={"Authorization": f"Bearer {token}"})
    pc1 = \
        db.session.\
            query(ProjectCleanup).\
            filter(ProjectCleanup.project_cleanup_id==project_cleanup1.project_cleanup_id).\
            one_or_none()
    assert pc1.status == 'USER_NOTIFIED'
    pc2 = \
        db.session.\
            query(ProjectCleanup).\
            filter(ProjectCleanup.project_cleanup_id==project_cleanup2.project_cleanup_id).\
            one_or_none()
    assert pc2.status == 'NOT_STARTED'

def test_mark_db_cleanup_finished(db, test_client):
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
    res = \
        test_client.post(
            "/api/v1/security/login",
            json={
                API_SECURITY_USERNAME_KEY: "admin",
                API_SECURITY_PASSWORD_KEY: "password",
                API_SECURITY_PROVIDER_KEY: "db"})
    assert res.status_code == 200
    token = \
        json.loads(res.data.decode("utf-8")).\
            get("access_token")
    res = \
        test_client.post(
            f'/api/v1/project_cleanup/mark_db_cleanup_finished/{project_cleanup1.project_cleanup_id}',
            headers={"Authorization": f"Bearer {token}"})
    pc1 = \
        db.session.\
            query(ProjectCleanup).\
            filter(ProjectCleanup.project_cleanup_id==project_cleanup1.project_cleanup_id).\
            one_or_none()
    assert pc1.status == 'DB_CLEANUP_FINISHED'
    pc2 = \
        db.session.\
            query(ProjectCleanup).\
            filter(ProjectCleanup.project_cleanup_id==project_cleanup2.project_cleanup_id).\
            one_or_none()
    assert pc2.status == 'NOT_STARTED'

def test_add_project_cleanup_data(db, test_client):
    res = \
        test_client.post(
            "/api/v1/security/login",
            json={
                API_SECURITY_USERNAME_KEY: "admin",
                API_SECURITY_PASSWORD_KEY: "password",
                API_SECURITY_PROVIDER_KEY: "db"})
    assert res.status_code == 200
    token = \
        json.loads(res.data.decode("utf-8")).\
            get("access_token")
    file_data = \
        BytesIO(b"""[{
        "email_id": "a@b.com",
        "name": "A B",
        "projects": ["ProjectA", "ProjectB"]}, {
        "email_id": "c@e.com",
        "name": "C E",
        "projects": ["ProjectC", "ProjectE"]}]""")
    res = \
        test_client.post(
            '/api/v1/project_cleanup/add_project_cleanup_data',
            headers={"Authorization": f"Bearer {token}"},
            data=dict(file=(file_data, 'test.json')),
            content_type='multipart/form-data',
            follow_redirects=True)
    assert res.status_code == 200
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