import json
import os
import tempfile
from io import BytesIO
from app.models import PreDeMultiplexingData
from app.pre_demultiplexing_data_api import (
    load_predemult_report,
    async_load_predemult_report,
    PreDeMultiplexingDataApi)
from flask_appbuilder.const import (
    API_SECURITY_PASSWORD_KEY,
    API_SECURITY_PROVIDER_KEY,
    API_SECURITY_REFRESH_KEY,
    API_SECURITY_USERNAME_KEY)

def test_load_predemult_report(db, tmp_path):
    temp_report_dir = \
        tempfile.mkdtemp(dir=tmp_path)
    temp_base_dir = \
        tempfile.mkdtemp(dir=tmp_path)
     # Create a dummy report
    temp_report_path = os.path.join(temp_report_dir, 'report.html')
    with open(temp_report_path, 'w') as fp:
        fp.write('<h1>Its as test report</h1>')
    load_predemult_report(
        run_name='test1',
        tag_name='test 1',
        file_path=temp_report_path,
        base_path=temp_base_dir)
    # check if its loaded
    record = db.session.query(PreDeMultiplexingData).filter_by(run_name='test1').first()
    assert record is not None
    assert record.run_name == 'test1'
    assert record.samplesheet_tag == 'test 1'
    assert os.path.basename(record.file_path) == 'report.html'
    assert os.path.exists(record.file_path)
    assert record.file_path != temp_report_path
    assert temp_base_dir in record.file_path

def test_async_load_predemult_report(db, tmp_path):
    temp_report_dir = \
        tempfile.mkdtemp(dir=tmp_path)
    temp_base_dir = \
        tempfile.mkdtemp(dir=tmp_path)
     # Create a dummy report
    temp_report_path = os.path.join(temp_report_dir, 'report.html')
    with open(temp_report_path, 'w') as fp:
        fp.write('<h1>Its as test report</h1>')
    async_load_predemult_report(
       run_name='test1',
        tag_name='test 1',
        file_path=temp_report_path,
        base_path=temp_base_dir)
    # check if its loaded
    record = db.session.query(PreDeMultiplexingData).filter_by(run_name='test1').first()
    assert record is not None
    assert record.run_name == 'test1'
    assert record.samplesheet_tag == 'test 1'
    assert os.path.basename(record.file_path) == 'report.html'
    assert os.path.exists(record.file_path)
    assert record.file_path != temp_report_path
    assert temp_base_dir in record.file_path

def test_PreDeMultiplexingDataApi1(db, test_client, tmp_path):
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
    # temp_base_dir = \
    #     tempfile.mkdtemp(dir=tmp_path)
    # app.config['REPORT_UPLOAD_PATH'] = temp_base_dir
    report_file_data = \
        BytesIO(b'<h1>Its as test report</h1>')
    res = \
        test_client.post(
            '/api/v1/predemultiplexing_data/add_report',
            data=dict(file=(report_file_data, 'report.html'),run_name="test1",samplesheet_tag="test 1"),
            headers={"Authorization": f"Bearer {token}"},
            content_type='multipart/form-data')
    assert res.status_code == 200
    assert json.loads(res.data.decode('utf-8')).get("message") == 'successfully submitted demult report loading job for report.html'
