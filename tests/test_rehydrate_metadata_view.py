import os
import requests
from unittest.mock import patch, MagicMock
from app.models import Project
from app.rehydrate_metadata_view import (
    async_trigger_airflow_pipeline,
    action_fetch_metadata
)


# @patch(
#     'app.rehydrate_metadata_view.trigger_airflow_pipeline',
#     return_value=requests.patch(
#         'https://httpbin.org/patch',
#         data={'key': 'value'},
#         timeout=5,
#         headers={'Content-Type': 'application/json'}))
# def test_async_trigger_airflow_pipeline(mock_object, db, tmp_path):
#     try:
#         project = Project(
#             project_igf_id='test_project_1',
#             deliverable='FASTQ',
#             status='ACTIVE'
#         )
#         db.session.add(project)
#         db.session.flush()
#         db.session.commit()
#     except Exception:
#         db.session.rollback()
#         raise
#     os.environ['AIRFLOW_CONF_FILE'] = tmp_path.as_posix()
#     result = async_trigger_airflow_pipeline(
#         'test_dag', [project.project_id])
#     assert project.project_id in result


@patch(
    'app.rehydrate_metadata_view.trigger_airflow_pipeline',
    return_value=requests.patch(
        'https://httpbin.org/patch',
        data={'key': 'value'},
        timeout=5,
        headers={'Content-Type': 'application/json'}))
def test_async_trigger_airflow_pipeline_multiple(mock_object, db, tmp_path):
    try:
        p1 = Project(
            project_igf_id='test_project_1',
            deliverable='FASTQ',
            status='ACTIVE')
        p2 = Project(
            project_igf_id='test_project_2',
            deliverable='ALIGNMENT',
            status='ACTIVE')
        db.session.add(p1)
        db.session.add(p2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    os.environ['AIRFLOW_CONF_FILE'] = tmp_path.as_posix()
    result = async_trigger_airflow_pipeline(
        'test_dag', [p1.project_id, p2.project_id])
    assert p1.project_id in result
    assert p2.project_id in result


@patch(
    'app.rehydrate_metadata_view.async_trigger_airflow_pipeline.apply_async',
    return_value=MagicMock())
@patch(
    'app.rehydrate_metadata_view.get_airflow_dag_id',
    return_value='test_dag')
def test_action_fetch_metadata_single_item(
    mock_dag_id, mock_async, db, tmp_path
):
    try:
        project = Project(
            project_igf_id='test_project_1',
            deliverable='FASTQ',
            status='ACTIVE'
        )
        db.session.add(project)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    os.environ['AIRFLOW_CONF_FILE'] = tmp_path.as_posix()
    result = action_fetch_metadata(project)
    assert len(result) == 1
    assert project.project_id in result
    mock_async.assert_called_once()


@patch(
    'app.rehydrate_metadata_view.async_trigger_airflow_pipeline.apply_async',
    return_value=MagicMock())
@patch(
    'app.rehydrate_metadata_view.get_airflow_dag_id',
    return_value='test_dag')
def test_action_fetch_metadata_list(
    mock_dag_id, mock_async, db, tmp_path
):
    try:
        p1 = Project(
            project_igf_id='test_project_1',
            deliverable='FASTQ',
            status='ACTIVE')
        p2 = Project(
            project_igf_id='test_project_2',
            deliverable='ALIGNMENT',
            status='ACTIVE')
        db.session.add(p1)
        db.session.add(p2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    os.environ['AIRFLOW_CONF_FILE'] = tmp_path.as_posix()
    result = action_fetch_metadata([p1, p2])
    assert len(result) == 2
    assert p1.project_id in result
    assert p2.project_id in result
    mock_async.assert_called_once()


@patch(
    'app.rehydrate_metadata_view.async_trigger_airflow_pipeline.apply_async',
    return_value=MagicMock())
@patch(
    'app.rehydrate_metadata_view.get_airflow_dag_id',
    return_value='test_dag')
def test_action_fetch_metadata_skips_cosmx(
    mock_dag_id, mock_async, db, tmp_path
):
    try:
        p1 = Project(
            project_igf_id='test_project_1',
            deliverable='COSMX',
            status='ACTIVE')
        p2 = Project(
            project_igf_id='test_project_2',
            deliverable='FASTQ',
            status='ACTIVE')
        db.session.add(p1)
        db.session.add(p2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    os.environ['AIRFLOW_CONF_FILE'] = tmp_path.as_posix()
    result = action_fetch_metadata([p1, p2])
    assert len(result) == 1
    assert p1.project_id not in result
    assert p2.project_id in result


@patch(
    'app.rehydrate_metadata_view.async_trigger_airflow_pipeline.apply_async',
    return_value=MagicMock())
@patch(
    'app.rehydrate_metadata_view.get_airflow_dag_id',
    return_value='test_dag')
def test_action_fetch_metadata_all_cosmx_no_trigger(
    mock_dag_id, mock_async, db, tmp_path
):
    try:
        p1 = Project(
            project_igf_id='test_project_1',
            deliverable='COSMX',
            status='ACTIVE')
        db.session.add(p1)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    os.environ['AIRFLOW_CONF_FILE'] = tmp_path.as_posix()
    result = action_fetch_metadata([p1])
    assert len(result) == 0
    mock_async.assert_not_called()


@patch(
    'app.rehydrate_metadata_view.async_trigger_airflow_pipeline.apply_async',
    return_value=MagicMock())
@patch(
    'app.rehydrate_metadata_view.get_airflow_dag_id',
    return_value='test_dag')
def test_action_fetch_metadata_single_cosmx_skipped(
    mock_dag_id, mock_async, db, tmp_path
):
    try:
        project = Project(
            project_igf_id='test_project_cosmx',
            deliverable='COSMX',
            status='ACTIVE'
        )
        db.session.add(project)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    os.environ['AIRFLOW_CONF_FILE'] = tmp_path.as_posix()
    result = action_fetch_metadata(project)
    assert len(result) == 0
    mock_async.assert_not_called()
