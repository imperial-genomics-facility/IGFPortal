import os
import json
from io import BytesIO
from app.models import Project, Sample, IgfUser
from app.metadata_api import async_cleanup_and_load_new_data_to_metadata_tables
from flask_appbuilder.const import (
    API_SECURITY_PASSWORD_KEY,
    API_SECURITY_PROVIDER_KEY,
    API_SECURITY_REFRESH_KEY,
    API_SECURITY_USERNAME_KEY)

def test_metadata_api1(test_client):
    json_data = {
        "project": [{
            "project_id": 1,
            "project_igf_id": "test1"}]}
    json_data = \
        json.dumps(json_data)
    res = \
        test_client.post(
            '/api/v1/metadata/load_metadata',
            data=dict(file=(BytesIO(json_data.encode()), 'test.json')),
            content_type='multipart/form-data',
            follow_redirects=True)
    assert res.status_code != 200
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
    json_data = {
        "project": [{
            "project_id": 1,
            "project_igf_id": "test1"}]}
    json_data = \
        json.dumps(json_data)
    res = \
        test_client.post(
            '/api/v1/metadata/load_metadata',
            headers={"Authorization": f"Bearer {token}"},
            data=dict(file=(BytesIO(json_data.encode()), 'test.json')),
            content_type='multipart/form-data',
            follow_redirects=True)
    assert res.status_code == 200
    assert json.loads(res.data.decode('utf-8')).get("message") == 'successfully submitted metadata update job'



def test_async_cleanup_and_load_new_data_to_metadata_tables(db, tmp_path):
    project = \
        Project(
            project_id=2,
            project_igf_id="test2")
    try:
        db.session.add(project)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    result = \
        db.session.\
            query(Project).\
            filter(Project.project_igf_id=="test2").\
            one_or_none()
    assert result is not None
    assert result.project_id == 2
    json_data = {
        "project": [{
            "project_id": 1,
            "project_igf_id": "test2"}]}
    temp_json_file = \
        os.path.join(tmp_path, 'metadata_db.json')
    with open(temp_json_file, 'w') as fp:
        json.dump(json_data, fp)
    _ = \
        async_cleanup_and_load_new_data_to_metadata_tables(
            temp_json_file)
    result = \
        db.session.\
            query(Project).\
            filter(Project.project_igf_id=="test2").\
            one_or_none()
    assert result is not None
    assert result.project_id == 1
