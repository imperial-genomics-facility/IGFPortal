import json
import os
import tempfile
from io import BytesIO
from app.models import AnalysesQCData
from app.analyses_qc_data_api import (
    load_analyses_qc_report,
    async_load_analyses_qc_report,
    AnalysesQCDataApi)
from flask_appbuilder.const import (
    API_SECURITY_PASSWORD_KEY,
    API_SECURITY_PROVIDER_KEY,
    API_SECURITY_REFRESH_KEY,
    API_SECURITY_USERNAME_KEY)

def test_load_analyses_qc_report(db, tmp_path):
    temp_report_dir = \
        tempfile.mkdtemp(dir=tmp_path)
    temp_base_dir = \
        tempfile.mkdtemp(dir=tmp_path)
     # Create a dummy report
    temp_report_path = os.path.join(temp_report_dir, 'report.html')
    with open(temp_report_path, 'w') as fp:
        fp.write('<h1>Its as test report</h1>')
    load_analyses_qc_report(
        analysis_name='test1',
        analysis_type='test1',
        qc_tag='test 1',
        file_path=temp_report_path,
        base_path=temp_base_dir)
    # check if its loaded
    record = db.session.query(AnalysesQCData).filter_by(analysis_name='test1').first()
    assert record is not None
    assert record.analysis_name == 'test1'
    assert record.analysis_type == 'test1'
    assert record.qc_tag == 'test 1'
    assert os.path.basename(record.file_path) == 'report.html'
    assert os.path.exists(record.file_path)
    assert record.file_path != temp_report_path
    assert temp_base_dir in record.file_path

def test_async_load_analyses_qc_report(db, tmp_path):
    temp_report_dir = \
        tempfile.mkdtemp(dir=tmp_path)
    temp_base_dir = \
        tempfile.mkdtemp(dir=tmp_path)
     # Create a dummy report
    temp_report_path = os.path.join(temp_report_dir, 'report.html')
    with open(temp_report_path, 'w') as fp:
        fp.write('<h1>Its as test report</h1>')
    async_load_analyses_qc_report(
       analysis_name='test1',
       analysis_type='test1',
       qc_tag='test 1',
       file_path=temp_report_path,
       base_path=temp_base_dir)
    # check if its loaded
    record = db.session.query(AnalysesQCData).filter_by(analysis_name='test1').first()
    assert record is not None
    assert record.analysis_name == 'test1'
    assert record.analysis_type == 'test1'
    assert record.qc_tag == 'test 1'
    assert os.path.basename(record.file_path) == 'report.html'
    assert os.path.exists(record.file_path)
    assert record.file_path != temp_report_path
    assert temp_base_dir in record.file_path

def test_AnalysesQCDataApi(db, test_client, tmp_path):
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
    report_file_data = \
        BytesIO(b'<h1>Its as test report</h1>')
    res = \
        test_client.post(
            '/api/v1/analyses_qc_data/add_report',
            data=dict(file=(report_file_data, 'report.html'),analysis_name="test1",analysis_type="test1",qc_tag="test 1"),
            headers={"Authorization": f"Bearer {token}"},
            content_type='multipart/form-data')
    assert res.status_code == 200
    assert json.loads(res.data.decode('utf-8')).get("message") == 'successfully submitted analyses qc report loading job for report.html'
