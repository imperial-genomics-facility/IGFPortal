import json
import requests
from urllib.parse import urljoin
from typing import Union

def get_airflow_dag_id(airflow_conf_file: str, dag_tag: str) -> Union[str, None]:
    try:
        with open(airflow_conf_file, "r") as fp:
            airflow_conf = json.load(fp)
        dag_id = airflow_conf.get(dag_tag)
        return dag_id
    except Exception as e:
        raise ValueError(
            f"Failed to get dag id for tag {dag_tag} in config file {airflow_conf_file}, error: {e}")


def post_to_airflow_api(
      airflow_conf_file: str,
      url_suffix: str,
      data: dict,
      headers: dict = {"Content-Type": "application/json"},
      verify: bool = False):
    try:
        with open(airflow_conf_file, "r") as fp:
            airflow_conf = json.load(fp)
        if 'url' not in airflow_conf or \
           'username' not in airflow_conf or \
           'password' not in airflow_conf:
            raise KeyError("Missing url, username or password key in conf file")
        data = json.dumps(data)
        url = \
            urljoin(airflow_conf['url'], url_suffix)
        res = \
        requests.post(
            url=url,
            data=data,
            headers=headers,
            auth=(airflow_conf["username"], airflow_conf["password"]),
            verify=verify)
        if res.status_code != 200:
            raise ValueError(
                f"Failed post request, got status: {res.status_code}")
        return res
    except Exception as e:
        raise ValueError(f"Failed to post to airflow, error: {e}")


def trigger_airflow_pipeline(
      dag_id: str,
      conf_data: dict,
      airflow_conf_file: str):
    try:
        url_suffix = \
            f'dags/{dag_id}/dagRuns'
        data = {"conf": conf_data}
        res = \
        post_to_airflow_api(
            airflow_conf_file=airflow_conf_file,
            url_suffix=url_suffix,
            data=data)
        return res
    except Exception as e:
        raise ValueError(
                f"Failed to trigger to airflow pipeline {dag_id}, error: {e}")