import json
import os
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
            deletion_date=datetime.now()+timedelta(days=15))
    project_cleanup2 = \
        ProjectCleanup(
            user_email='f@h.com',
            user_name='f h',
            projects='["ProjectC", "ProjectD"]',
            deletion_date=datetime.now()+timedelta(days=15))
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