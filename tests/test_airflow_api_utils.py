import os
import json
import requests
from unittest.mock import patch
from app.airflow.airflow_api_utils import (
    get_airflow_dag_id,
    post_to_airflow_api,
    trigger_airflow_pipeline
)

@patch('app.airflow.airflow_api_utils.requests')
def test_get_airflow_dag_id(mock_requests, tmp_path):
    # Create a mock response
    mock_response = mock_requests.get.return_value
    mock_response.json.return_value = {
        "dags": [
            {"dag_id": "dag23_test_bclconvert_demult", "tags": [{"name": "de_multiplexing_test_barcode_dag"}]},
            {"dag_id": "dag24_build_bclconvert_dynamic_dags", "tags": [{"name": "de_multiplexing_production_dag"}]}
        ]
    }
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


@patch('app.airflow.airflow_api_utils.requests')
def test_post_to_airflow_api(mock_requests, tmp_path):
    # Create a mock response
    mock_response = mock_requests.post.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = {"key": "response"}
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
    _ = post_to_airflow_api(
        airflow_conf_file=config_file_path,
        url_suffix="test",
        data={"key": "val"},
        dry_run=True
    )
    mock_requests.post.assert_called_once()
    mock_requests.post.assert_called_with(
        url="https://airflow.test/api/v1/test",
        data=json.dumps({"key": "val"}),
        headers={"Content-Type": "application/json"},
        auth=("airflow", "airflow"),
        verify=False
    )


@patch('app.airflow.airflow_api_utils.requests')
def test_trigger_airflow_pipeline(mock_requests, tmp_path):
    # Create a mock response
    mock_response = mock_requests.post.return_value
    mock_response.status_code = 200
    mock_response.json.return_value = {"dag_run_id": "test_run_123"}
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
    _ = trigger_airflow_pipeline(
        dag_id="dag23_test_bclconvert_demult",
        conf_data={"key": "value"},
        airflow_conf_file=config_file_path,
        dry_run=True
    )
    mock_requests.post.assert_called_once()
    mock_requests.post.assert_called_with(
        url="https://airflow.test/api/v1/dags/dag23_test_bclconvert_demult/dagRuns",
        data=json.dumps({"conf": {"key": "value"}}),
        headers={"Content-Type": "application/json"},
        auth=("airflow", "airflow"),
        verify=False
    )