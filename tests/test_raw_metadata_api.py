import json
import os
from io import BytesIO
from app.models import (
    RawMetadataModel)
from flask_appbuilder.const import (
    API_SECURITY_PASSWORD_KEY,
    API_SECURITY_PROVIDER_KEY,
    API_SECURITY_REFRESH_KEY,
    API_SECURITY_USERNAME_KEY)

def test_raw_metadata_api1(db, test_client, tmp_path):
    metadata1 = \
        RawMetadataModel(
            metadata_tag='test1',
            raw_csv_data='raw',
            formatted_csv_data='formatted',
            report='')
    try:
        db.session.add(metadata1)
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
        test_client.get(
            '/api/v1/raw_metadata/search_new_metadata',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400
    res = \
        test_client.get(
            '/api/v1/raw_metadata/search_new_metadata',
            headers={"Authorization": f"Bearer {token}"},
            data=dict(
                file=(
                    BytesIO(b'{"project_list":["test1", "test3", "test4", "test5"]}'),
                    'test.json')),
            content_type='multipart/form-data',
            follow_redirects=True)
    assert res.status_code == 200
    assert 'new_projects' in res.data.decode('utf-8')
    assert 'test3' in json.loads(res.data.decode('utf-8')).get('new_projects').split(",")
    assert 'test4' in json.loads(res.data.decode('utf-8')).get('new_projects').split(",")
    assert 'test5' in json.loads(res.data.decode('utf-8')).get('new_projects').split(",")
    assert len(json.loads(res.data.decode('utf-8')).get('new_projects').split(",")) == 3
    res = \
        test_client.get(
            '/api/v1/raw_metadata/search_new_metadata',
            headers={"Authorization": f"Bearer {token}"},
            data=dict(file=(BytesIO(b'{"project_list":["test1"]}'), 'test.json')),
            content_type='multipart/form-data',
            follow_redirects=True)
    assert res.status_code == 200
    assert 'new_projects' in res.data.decode('utf-8')
    assert json.loads(res.data.decode('utf-8')).get('new_projects') == ""
    res = \
        test_client.get(
            '/api/v1/raw_metadata/search_new_metadata',
            headers={"Authorization": f"Bearer {token}"},
            data=dict(file=(BytesIO(b'{"project_list":["test2"]}'), 'test.json')),
            content_type='multipart/form-data',
            follow_redirects=True)
    assert res.status_code == 200
    assert 'new_projects' in res.data.decode('utf-8')
    assert json.loads(res.data.decode('utf-8')).get('new_projects') == "test2"
    metadata_file_data = \
        BytesIO(
            b'[{"metadata_tag": "test2", "raw_csv_data": [{"project_id": "c","sample_id": "d"}], '
            b'"formatted_csv_data": [{"project_id": "c","sample_id": "d"}]}]')
    res = \
        test_client.post(
            '/api/v1/raw_metadata/add_metadata',
            headers={"Authorization": f"Bearer {token}"},
            data=dict(file=(metadata_file_data, 'test.json')),
            content_type='multipart/form-data',
            follow_redirects=True)
    assert res.status_code == 200
    res = \
        test_client.get(
            '/api/v1/raw_metadata/search_new_metadata',
            headers={"Authorization": f"Bearer {token}"},
            data=dict(file=(BytesIO(b'{"project_list":["test2"]}'), 'test.json')),
            content_type='multipart/form-data',
            follow_redirects=True)
    assert res.status_code == 200
    assert 'new_projects' in res.data.decode('utf-8')
    assert json.loads(res.data.decode('utf-8')).get('new_projects') == ""
    res = \
        test_client.get(
            '/api/v1/raw_metadata/download_ready_metadata',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.data.decode('utf-8').strip() == '{}'
    metadata3 = \
        RawMetadataModel(
            metadata_tag='test3',
            raw_csv_data='[{"project_id": "c","sample_id": "d"}]',
            formatted_csv_data='[{"project_id": "c","sample_id": "d"}]',
            status='READY',
            report='')
    try:
        db.session.add(metadata3)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    res = \
        test_client.get(
            '/api/v1/raw_metadata/download_ready_metadata',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    json_data = \
        json.loads(res.data.decode('utf-8'))
    assert 'test3' in json_data
    assert json_data.get('test3') == '[{"project_id": "c","sample_id": "d"}]'
    res = \
        test_client.get(
            f'/api/v1/raw_metadata/mark_ready_metadata_as_synced',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    records = \
        db.session.\
            query(RawMetadataModel.status).\
            filter(RawMetadataModel.raw_metadata_id==metadata3.raw_metadata_id).\
            one_or_none()
    assert records is not None
    assert records[0] == 'SYNCHED'
    metadata4 = \
        RawMetadataModel(
            raw_metadata_id=4,
            metadata_tag='test4',
            raw_csv_data='[{"project_id": "c","sample_id": "d"}]',
            formatted_csv_data='[{"project_id": "c","sample_id": "d"}]',
            status='READY',
            report='')
    try:
        db.session.add(metadata4)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    assert res.status_code == 200
    res = \
        test_client.get(
            '/api/v1/raw_metadata/get_raw_metadata/4',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    json_data = \
        json.loads(res.data.decode('utf-8'))
    assert 'test4' in json_data
    assert json_data.get('test4') == '[{"project_id": "c","sample_id": "d"}]'
    res = \
        test_client.get(
            '/api/v1/raw_metadata/mark_ready_metadata_as_synced/4',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    records = \
        db.session.\
            query(RawMetadataModel.status).\
            filter(RawMetadataModel.raw_metadata_id==4).\
            one_or_none()
    assert records is not None
    assert records[0] == 'SYNCHED'

