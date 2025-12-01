import os
import json
import requests
from unittest.mock import patch
from app.airflow.airflow_api_utils import (
    get_airflow_dag_id,
    post_to_airflow_api,
    trigger_airflow_pipeline
)

@patch(
    'app.airflow.airflow_api_utils.requests',
    return_value=requests.patch(
        'https://httpbin.org/patch',
        data ={'key': 'value'},
        headers={'Content-Type': 'application/json'}
    )
)
def test_get_airflow_dag_id(
    mock_object,
    tmp_path):
    config_file_path = os.path.join(
        tmp_path,
        'airflow_conf.json'
    )
    conf_data = {
        "url": "https://airflow.test/api/v1/",
        "username": "airflow",
        "password": "airflow",
        "de_multiplexing_test_barcode_dag": "dag23_test_bclconvert_demult",
        "de_multiplexing_production_dag": "dag24_build_bclconvert_dynamic_dags",
        "de_multiplexing_cleanup_dag": "dag27_cleanup_demultiplexing_output"
    }
    with open(config_file_path, "w") as fp:
        json.dump(conf_data, fp)
    assert os.path.exists(config_file_path)
    dag_id = get_airflow_dag_id(
        airflow_conf_file=os.path.abspath(config_file_path),
        dag_tag="de_multiplexing_test_barcode_dag")
    assert dag_id == "dag23_test_bclconvert_demult"
    dag_id = get_airflow_dag_id(
        airflow_conf_file=config_file_path,
        dag_tag="no match")
    assert dag_id is None


@patch(
    'app.airflow.airflow_api_utils.requests',
    return_value=requests.patch(
        'https://httpbin.org/patch',
        data=json.dumps({'key': 'value'}),
        headers={'Content-Type': 'application/json'}
    )
)
def test_post_to_airflow_api(mock_object, tmp_path):
    config_file_path = os.path.join(
        tmp_path,
        'airflow_conf.json'
    )
    conf_data = {
        "url": "https://airflow.test/api/v1/",
        "username": "airflow",
        "password": "airflow",
        "de_multiplexing_test_barcode_dag": "dag23_test_bclconvert_demult",
        "de_multiplexing_production_dag": "dag24_build_bclconvert_dynamic_dags",
        "de_multiplexing_cleanup_dag": "dag27_cleanup_demultiplexing_output"
    }
    with open(config_file_path, "w") as fp:
        json.dump(conf_data, fp)
    res = post_to_airflow_api(
        airflow_conf_file=config_file_path,
        url_suffix="test",
        data={"key": "val"},
        dry_run=True
    )
    mock_object.post.assert_called_once()
    mock_object.post.assert_called_with(
        url="https://airflow.test/api/v1/test",
        data=json.dumps({"key": "val"}),
        headers={"Content-Type": "application/json"},
        auth=("airflow", "airflow"),
        verify=False
    )


@patch(
    'app.airflow.airflow_api_utils.requests',
    return_value=requests.patch(
        'https://httpbin.org/patch',
        data ={'key': 'value'},
        headers={'Content-Type': 'application/json'}
    )
)
def test_trigger_airflow_pipeline(mock_object, tmp_path):
    config_file_path = os.path.join(
        tmp_path,
        'airflow_conf.json'
    )
    conf_data = {
        "url": "https://airflow.test/api/v1/",
        "username": "airflow",
        "password": "airflow",
        "de_multiplexing_test_barcode_dag": "dag23_test_bclconvert_demult",
        "de_multiplexing_production_dag": "dag24_build_bclconvert_dynamic_dags",
        "de_multiplexing_cleanup_dag": "dag27_cleanup_demultiplexing_output"
    }
    with open(config_file_path, "w") as fp:
        json.dump(conf_data, fp)
    res = trigger_airflow_pipeline(
        dag_id="dag23_test_bclconvert_demult",
        conf_data={"key": "value"},
        airflow_conf_file=config_file_path,
        dry_run=True
    )
    mock_object.post.assert_called_once()
    mock_object.post.assert_called_with(
        url="https://airflow.test/api/v1/dags/dag23_test_bclconvert_demult/dagRuns",
        data=json.dumps({"conf": {"key": "value"}}),
        headers={"Content-Type": "application/json"},
        auth=("airflow", "airflow"),
        verify=False
    )