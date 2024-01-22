from app.admin_home_api import async_parse_and_add_new_admin_view_data
from app.models import AdminHomeData
import os, json
from io import BytesIO
from unittest.mock import patch
from flask_appbuilder.const import (
    API_SECURITY_PASSWORD_KEY,
    API_SECURITY_PROVIDER_KEY,
    API_SECURITY_REFRESH_KEY,
    API_SECURITY_USERNAME_KEY)

def test_admin_home_api1(db, test_client):
    results = \
        db.session.\
            query(AdminHomeData).\
            filter(AdminHomeData.admin_data_tag=='test').\
            one_or_none()
    assert results is None
    json_data = {
            'admin_data_tag': 'test',
            'recent_finished_runs': 1,
            'recent_finished_analysis': 1,
            'ongoing_runs': 1,
            'ongoing_analysis': 1,
            'sequence_counts_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]},
            'storage_stat_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]}
        }
    json_data = \
        json.dumps(json_data)
    res = \
        test_client.post(
            '/api/v1/admin_home/update_admin_view_data',
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
            'admin_data_tag': 'test',
            'recent_finished_runs': 1,
            'recent_finished_analysis': 1,
            'ongoing_runs': 1,
            'ongoing_analysis': 1,
            'sequence_counts_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]},
            'storage_stat_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]}
        }
    json_data = \
        json.dumps(json_data)
    res = \
        test_client.post(
            '/api/v1/admin_home/update_admin_view_data',
            headers={"Authorization": f"Bearer {token}"},
            data=dict(file=(BytesIO(json_data.encode()), 'test.json')),
            content_type='multipart/form-data',
            follow_redirects=True)
    assert res.status_code == 200
    assert json.loads(res.data.decode('utf-8')).get("message") == 'loaded new data'


def test_async_parse_and_add_new_admin_view_data(db, tmp_path):
    json_data = {
            'admin_data_tag': 'test',
            'recent_finished_runs': 1,
            'recent_finished_analysis': 1,
            'ongoing_runs': 1,
            'ongoing_analysis': 1,
            'sequence_counts_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]},
            'storage_stat_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]}
        }
    temp_json_file = \
        os.path.join(
            tmp_path,
            'admin_home1.json')
    with open(temp_json_file, 'w') as fp:
        json.dump(json_data, fp)
    _ = \
        async_parse_and_add_new_admin_view_data(
            temp_json_file)
    results = \
        db.session.\
            query(AdminHomeData).\
            filter(AdminHomeData.admin_data_tag=='test').\
            one_or_none()
    assert results is not None
    assert results.recent_finished_runs == 1
    assert isinstance(results.sequence_counts_plot, str)
    json_data = {
        'admin_data_tag': 'test',
        'recent_finished_runs': 2,
        'recent_finished_analysis': 1,
        'ongoing_runs': 1,
        'ongoing_analysis': 1,
        'sequence_counts_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]},
        'storage_stat_plot': {'labels': ['a', 'b', 'c'], 'datasets': [{'label': 'test1', 'data': [0, 1, 2]}]}}
    temp_json_file = \
        os.path.join(
            tmp_path,
            'admin_home2.json')
    with open(temp_json_file, 'w') as fp:
        json.dump(json_data, fp)
    _ = \
        async_parse_and_add_new_admin_view_data(
            temp_json_file)
    results = \
        db.session.\
            query(AdminHomeData).\
            filter(AdminHomeData.admin_data_tag=='test').\
            one_or_none()
    assert results is not None
    assert results.recent_finished_runs == 2