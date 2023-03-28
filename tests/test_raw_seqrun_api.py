import json
import os
from io import BytesIO
from app.models import (
    RawSeqrun,
    SampleSheetModel)
from flask_appbuilder.const import (
    API_SECURITY_PASSWORD_KEY,
    API_SECURITY_PROVIDER_KEY,
    API_SECURITY_REFRESH_KEY,
    API_SECURITY_USERNAME_KEY)

def test_raw_seqrun_api(db, test_client, tmp_path):
    # with test_client.session_transaction() as session:
    #     session['user_id'] = 1
    #     session['_fresh'] = True
    res = \
        test_client.post(
            "/api/v1/security/login",
            json={
                API_SECURITY_USERNAME_KEY: "admin",
                API_SECURITY_PASSWORD_KEY: "password",
                API_SECURITY_PROVIDER_KEY: "db"})
    # res = test_client.get('/raw_analysis/search_new_analysis')
    # res = res.json()
    assert res.status_code == 200
    token = \
        json.loads(res.data.decode("utf-8")).\
            get("access_token")
    res = \
        test_client.post(
            '/api/v1/raw_seqrun/add_new_seqrun',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 400
    raw_seqrun1 = \
        RawSeqrun(raw_seqrun_igf_id='run1')
    try:
        db.session.add(raw_seqrun1)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    records = \
        db.session.\
            query(RawSeqrun.raw_seqrun_igf_id).\
            filter(RawSeqrun.raw_seqrun_igf_id=="run3").\
            one_or_none()
    assert records is None
    res = \
        test_client.post(
            '/api/v1/raw_seqrun/add_new_seqrun',
            headers={"Authorization": f"Bearer {token}"},
            data=dict(file=(BytesIO(b'{"seqrun_id_list":["run1", "run2", "run3"]}'), 'test.json')),
            content_type='multipart/form-data',
            follow_redirects=True)
    assert res.status_code == 200
    records = \
        db.session.\
            query(RawSeqrun.raw_seqrun_igf_id).\
            filter(RawSeqrun.raw_seqrun_igf_id=="run3").\
            one_or_none()
    assert records is not None