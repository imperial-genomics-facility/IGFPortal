from unittest.mock import patch
from app.models import (
    RawCosMxMetadataBuilder,
    RawCosMxMetadataModel
)
from app.cosmx_raw_metadata_view import (
    async_validate_and_register_cosmx_metadata,
    action_validate_and_register_cosmx_metadata,
    action_resubmit_cosmx_metadata,
    async_resubmit_cosmx_metadata
)

def test_action_resubmit_cosmx_metadata(db):
    raw_metadata1 = RawCosMxMetadataModel(
        cosmx_metadata_tag="test1"
    )
    try:
        db.session.add(raw_metadata1)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
    with patch(
        'app.cosmx_raw_metadata_view.async_resubmit_cosmx_metadata',
        return_values={"AAA": "BBB"}
    ):
        project_list, _ = action_resubmit_cosmx_metadata(
            item=[raw_metadata1]
        )
    assert len(project_list) == 1
    assert raw_metadata1.cosmx_metadata_tag in project_list


def test_async_resubmit_cosmx_metadata():
    with patch('app.cosmx_raw_metadata_view.get_airflow_dag_id') as  mock_get_airflow_dag_id:
        with patch('app.cosmx_raw_metadata_view.trigger_airflow_pipeline') as mock_trigger_airflow_pipeline:
            with patch.dict('os.environ', {'AIRFLOW_CONF_FILE': 'test_conf'}):
                results = async_resubmit_cosmx_metadata(
                    id_list=[1, 2, 3]
                )
                mock_get_airflow_dag_id.assert_called()
                mock_trigger_airflow_pipeline.assert_called()
    assert len(results) == 3
    assert 1 in results


def test_action_validate_and_register_cosmx_metadata(db):
    raw_data1 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=1,
        cosmx_metadata_tag="test_prj_1",
        name="My Name",
        email_id="my@email.com",
        username="test1123"
    )
    raw_data2 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=2,
        cosmx_metadata_tag="test",
        name="My",
        email_id="myemail.com",
        username="test"
    )
    try:
        db.session.add(raw_data1)
        db.session.add(raw_data2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    with patch(
        'app.cosmx_raw_metadata_view.async_validate_and_register_cosmx_metadata',
        return_values={"AAA": "BBB"}
    ):
        project_list, _ = action_validate_and_register_cosmx_metadata(
            item=[raw_data1, raw_data2]
        )
    assert len(project_list) == 2
    assert raw_data1.cosmx_metadata_tag in project_list


def test_async_validate_and_register_cosmx_metadata(db):
    raw_data1 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=1,
        cosmx_metadata_tag="test_prj_1",
        name="My Name",
        email_id="my@email.com",
        username="test1123"
    )
    raw_data2 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=2,
        cosmx_metadata_tag="test",
        name="My",
        email_id="myemail.com",
        username="test"
    )
    try:
        db.session.add(raw_data1)
        db.session.add(raw_data2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    ## valid design status
    with patch('app.cosmx_raw_metadata_view.get_airflow_dag_id') as  mock_get_airflow_dag_id:
        with patch('app.cosmx_raw_metadata_view.trigger_airflow_pipeline') as mock_trigger_airflow_pipeline:
            with patch.dict('os.environ', {'AIRFLOW_CONF_FILE': 'test_conf'}):
                results = async_validate_and_register_cosmx_metadata(
                    id_list=[raw_data1.raw_cosmx_metadata_builder_id]
                )
                assert raw_data1.raw_cosmx_metadata_builder_id in results
                assert results.get(raw_data1.raw_cosmx_metadata_builder_id) == 'VALIDATED'
                mock_get_airflow_dag_id.assert_called()
                mock_trigger_airflow_pipeline.assert_called()
                results = async_validate_and_register_cosmx_metadata(
                    id_list=[raw_data2.raw_cosmx_metadata_builder_id]
                )
                assert raw_data2.raw_cosmx_metadata_builder_id in results
                assert results.get(raw_data2.raw_cosmx_metadata_builder_id) == 'FAILED'