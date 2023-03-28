import json
import os
from app.models import (
    RawAnalysis,
    Project,
    Pipeline)
from flask_appbuilder.const import (
    API_SECURITY_PASSWORD_KEY,
    API_SECURITY_PROVIDER_KEY,
    API_SECURITY_REFRESH_KEY,
    API_SECURITY_USERNAME_KEY)

def test_raw_analysis_api1(db, test_client, tmp_path):
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
        test_client.get(
            '/api/v1/raw_analysis/search_new_analysis',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert json.loads(res.data.decode("utf-8")).get('new_projects') == []
    pipeline1 = \
        Pipeline(
            pipeline_name='pipeline1',
            pipeline_db='test')
    project1 = \
        Project(
            project_igf_id='project1')
    raw_analysis1 = \
        RawAnalysis(
            analysis_name='raw_analysis1',
            analysis_yaml='yaml_data',
            project=project1,
            pipeline=pipeline1,
            status='FAILED')
    analysis_yaml = """sample_metadata:
    sample1:
        condition: test
    sample2:
        condition: test
    """
    raw_analysis2 = \
        RawAnalysis(
            analysis_name='raw_analysis2',
            analysis_yaml=analysis_yaml,
            project=project1,
            pipeline=pipeline1,
            status='VALIDATED')
    try:
        db.session.add(pipeline1)
        db.session.add(project1)
        db.session.add(raw_analysis1)
        db.session.add(raw_analysis2)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    res = \
        test_client.get(
            '/api/v1/raw_analysis/search_new_analysis',
            headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    assert json.loads(res.data.decode("utf-8")).get('new_projects') == [2]
    res = \
        test_client.post(
            '/api/v1/raw_analysis/get_raw_analysis_data/2',
            headers={"Authorization": f"Bearer {token}"})
    json_file = \
        os.path.join(tmp_path, 'raw_analysis1.json')
    with open(json_file, 'wb') as fp:
        fp.write(res.data)
    with open(json_file, 'r') as fp:
        json_data = json.load(fp)
    assert 'analysis_name' in json_data
    assert json_data.get('analysis_name') == 'raw_analysis2'
    assert 'project_id' in json_data
    assert json_data.get('project_id') == project1.project_id
    assert 'pipeline_id' in json_data
    assert json_data.get('pipeline_id') == pipeline1.pipeline_id
    res = \
        test_client.post(
            '/api/v1/raw_analysis/get_raw_analysis_data/1',
            headers={"Authorization": f"Bearer {token}"})
    json_file = \
        os.path.join(tmp_path, 'raw_analysis2.json')
    with open(json_file, 'wb') as fp:
        fp.write(res.data)
    with open(json_file, 'r') as fp:
        json_data = json.load(fp)
    assert 'analysis_name' in json_data
    assert 'project_id' in json_data
    assert json_data.get('analysis_name') == ''
    assert json_data.get('project_id') == ''
    res = \
        test_client.post(
            '/api/v1/raw_analysis/get_raw_analysis_data/3',
            headers={"Authorization": f"Bearer {token}"})
    json_file = \
        os.path.join(tmp_path, 'raw_analysis3.json')
    with open(json_file, 'wb') as fp:
        fp.write(res.data)
    with open(json_file, 'r') as fp:
        json_data = json.load(fp)
    assert 'analysis_name' in json_data
    assert 'project_id' in json_data
    assert json_data.get('analysis_name') == ''
    assert json_data.get('project_id') == ''
    res = \
        test_client.post(
            '/api/v1/raw_analysis/mark_analysis_synched/2',
            headers={"Authorization": f"Bearer {token}"})
    assert json.loads(res.data.decode('utf-8')).get('status') == 'success'
    res = \
        test_client.post(
            '/api/v1/raw_analysis/mark_analysis_synched/1',
            headers={"Authorization": f"Bearer {token}"})
    assert json.loads(res.data.decode('utf-8')).get('status') == 'failed'
    res = \
        test_client.post(
            '/api/v1/raw_analysis/mark_analysis_synched/3',
            headers={"Authorization": f"Bearer {token}"})
    assert json.loads(res.data.decode('utf-8')).get('status') == 'failed'


