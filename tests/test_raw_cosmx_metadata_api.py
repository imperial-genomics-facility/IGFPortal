import json
from app.models import (
    RawCosMxMetadataModel
)
from flask_appbuilder.const import (
    API_SECURITY_PASSWORD_KEY,
    API_SECURITY_PROVIDER_KEY,
    API_SECURITY_USERNAME_KEY)

def test_raw_cosmx_metadata_api1(db, test_client, tmp_path):
    raw_metadata1 = RawCosMxMetadataModel(
        raw_cosmx_metadata_id=1,
        cosmx_metadata_tag="test1",
        formatted_csv_data='[{"project_id": "c","sample_id": "d"}]',
        status='READY'
    )
    try:
        db.session.add(raw_metadata1)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
    res = test_client.post(
        "/api/v1/security/login",
        json={
            API_SECURITY_USERNAME_KEY: "admin",
            API_SECURITY_PASSWORD_KEY: "password",
            API_SECURITY_PROVIDER_KEY: "db"
        }
    )
    assert res.status_code == 200
    token = (
        json
        .loads(
            res.data.decode("utf-8")
        )
        .get("access_token")
    )
    res = test_client.get(
        '/api/v1/raw_cosmx_metadata/get_raw_metadata/1',
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res.status_code == 200
    json_data = (
        json.loads(
            res.data.decode('utf-8')
        )
    )
    assert 'test1' in json_data
    assert json_data.get('test1') == '[{"project_id": "c","sample_id": "d"}]'
    res = \
        test_client.get(
            '/api/v1/raw_cosmx_metadata/mark_ready_metadata_as_synced/1',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    records = \
        db.session.\
            query(RawCosMxMetadataModel.status).\
            filter(RawCosMxMetadataModel.raw_cosmx_metadata_id==1).\
            one_or_none()
    assert records is not None
    assert records[0] == 'SYNCHED'