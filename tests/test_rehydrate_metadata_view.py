import os
import requests
from unittest.mock import patch, MagicMock
from app.models import (
    Project,
    Sample,
    Experiment,
    Run,
    Run_attribute
)
from app.rehydrate_metadata_view import (
    async_trigger_airflow_pipeline,
    action_fetch_metadata,
    RehydrateProjectMetadataView,
    get_sample_for_project
)


def test_get_sample_for_project(db):
    # project1: fastq, acttive, two samples, one flowcell lane
    pr1 = Project(
        project_id=1,
        project_igf_id="project1",
        deliverable="FASTQ",
        status="ACTIVE"
    )
    pr1_sa1 = Sample(
        sample_id=1,
        sample_igf_id="pr1_sample1",
        project_id=pr1.project_id
    )
    pr1_sa2 = Sample(
        sample_id=2,
        sample_igf_id="pr1_sample2",
        project_id=pr1.project_id
    )
    pr1_sa1_exp1 = Experiment(
        experiment_id=1,
        experiment_igf_id="pr1_sample1_lib",
        library_name="pr1_sample1_lib",
        sample_id=pr1_sa1.sample_id,
        project_id=pr1.project_id
    )
    pr1_sa2_exp1 = Experiment(
        experiment_id=2,
        experiment_igf_id="pr1_sample2_lib",
        library_name="pr1_sample2_lib",
        sample_id=pr1_sa2.sample_id,
        project_id=pr1.project_id
    )
    pr1_sa1_exp1_r1 = Run(
        run_id=1,
        run_igf_id="pr1_sample1_lib_f1_l1",
        lane_number='1',
        experiment_id=pr1_sa1_exp1.experiment_id
    )
    pr1_sa2_exp1_r1 = Run(
        run_id=2,
        run_igf_id="pr1_sample2_lib_f1_l1",
        lane_number='1',
        experiment_id=pr1_sa2_exp1.experiment_id
    )
    pr1_sa1_exp1_r1_a1 = Run_attribute(
        attribute_name="R1_READ_COUNT",
        attribute_value=1000,
        run_id=pr1_sa1_exp1_r1.run_id
    )
    pr1_sa2_exp1_r1_a1 = Run_attribute(
        attribute_name="R1_READ_COUNT",
        attribute_value=1001,
        run_id=pr1_sa2_exp1_r1.run_id
    )
    db.session.add(pr1)
    db.session.add(pr1_sa1)
    db.session.add(pr1_sa2)
    db.session.add(pr1_sa1_exp1)
    db.session.add(pr1_sa2_exp1)
    db.session.add(pr1_sa1_exp1_r1)
    db.session.add(pr1_sa2_exp1_r1)
    db.session.add(pr1_sa1_exp1_r1_a1)
    db.session.add(pr1_sa2_exp1_r1_a1)
    db.session.flush()
    db.session.commit()
    rows = get_sample_for_project(
        project_id=pr1.project_id,
        per_page=10,
        offset=0
    )
    assert len(rows) == 2
    assert len(rows[0]) == 4
    assert pr1.project_igf_id == rows[0][0]
    assert pr1_sa2.sample_igf_id == rows[0][1]
    assert int(rows[0][3]) == 1001

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
