import json
import os
from io import BytesIO
from app.models import (
    RawCosMxMetadataModel)
from flask_appbuilder.const import (
    API_SECURITY_PASSWORD_KEY,
    API_SECURITY_PROVIDER_KEY,
    API_SECURITY_REFRESH_KEY,
    API_SECURITY_USERNAME_KEY)

def test_download_ready_metadata_api(db, test_client, tmp_path):
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
            '/api/v1/raw_cosmx_metadata/download_ready_metadata',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert res.data.decode('utf-8').strip() == '{}'
    csv_data1 = """project_igf_id,name,email_id,username
    IGFQA-1234,testuser,test@user.com,testuser"""
    metadata1 = \
        RawCosMxMetadataModel(
            raw_cosmx_metadata_id=1,
            cosmx_metadata_tag='run1',
            formatted_csv_data=csv_data1.replace(" ", ""),
            status="FAILED",
            report='')
    metadata2 = \
        RawCosMxMetadataModel(
            raw_cosmx_metadata_id=2,
            cosmx_metadata_tag='run2',
            formatted_csv_data=csv_data1.replace(" ", ""),
            status="VALIDATED",
            report='')
    metadata3 = \
        RawCosMxMetadataModel(
            raw_cosmx_metadata_id=3,
            cosmx_metadata_tag='run3',
            formatted_csv_data=csv_data1.replace(" ", ""),
            status="VALIDATED",
            report='')
    try:
        db.session.add(metadata1)
        db.session.add(metadata2)
        db.session.add(metadata3)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    res = \
        test_client.get(
            '/api/v1/raw_cosmx_metadata/download_ready_metadata',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    json_data = \
        json.loads(res.data.decode('utf-8'))
    assert 'run3' in json_data
    assert json_data.get('run3') == \
        [{"project_igf_id": "IGFQA-1234","name": "testuser","email_id":"test@user.com","username":"testuser"}]
