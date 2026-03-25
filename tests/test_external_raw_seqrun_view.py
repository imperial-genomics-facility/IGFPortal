from unittest.mock import patch
from app.models import (
    Platform,
    RawExternalSeqrun
)
from app.external_raw_seqrun_view import (
    action_reject_raw_external_seqrun,
    _extract_platform_name_from_seqrun_id,
    _check_registered_seqrun_platform,
    action_add_raw_external_seqrun,
)

def test_extract_platform_name_from_seqrun_id():
    platform_name = _extract_platform_name_from_seqrun_id(
        seqrun_name="AABBCC_DD"
    )
    assert platform_name is None
    platform_name = _extract_platform_name_from_seqrun_id(
        seqrun_name="260124_AABBCCDD_100_EEFFGGHH110"
    )
    assert platform_name == "AABBCCDD"

def test_check_registered_seqrun_platform(db):
    platform1 = Platform(
        platform_igf_id="AABBCCDD",
        model_name="NOVASEQ6000",
        vendor_name="ILLUMINA",
        software_name="RTA"
    )
    db.session.add(platform1)
    db.session.flush()
    db.session.commit()
    db_results = _check_registered_seqrun_platform(
        platform_name="EEFFGGHH"
    )
    assert db_results is False
    db_results = _check_registered_seqrun_platform(
        platform_name="AABBCCDD"
    )
    assert db_results is True

def test_action_reject_raw_external_seqrun(db):
    raw_run1 = RawExternalSeqrun(
        raw_external_seqrun_igf_id="AABBCCDD",
        status="UNKNOWN"
    )
    raw_run2 = RawExternalSeqrun(
        raw_external_seqrun_igf_id="EEFFGGHH",
        status="UNKNOWN"
    )
    raw_run3 = RawExternalSeqrun(
        raw_external_seqrun_igf_id="IIJJKKLL",
        status="UNKNOWN"
    )
    db.session.add(raw_run1)
    db.session.add(raw_run2)
    db.session.add(raw_run3)
    db.session.flush()
    db.session.commit()
    action_reject_raw_external_seqrun(raw_run1)
    records = (
        db.session
        .query(RawExternalSeqrun.status)
        .filter(
            RawExternalSeqrun.raw_external_seqrun_igf_id=="AABBCCDD"
        )
        .all()
    )
    assert len(records) == 1
    assert records[0][0] == "REJECTED"
    records = (
        db.session
        .query(RawExternalSeqrun.status)
        .filter(
            RawExternalSeqrun.raw_external_seqrun_igf_id=="IIJJKKLL"
        )
        .all()
    )
    assert len(records) == 1
    assert records[0][0] == "UNKNOWN"
    action_reject_raw_external_seqrun([raw_run2])
    records = (
        db.session
        .query(RawExternalSeqrun.status)
        .filter(
            RawExternalSeqrun.raw_external_seqrun_igf_id=="EEFFGGHH"
        )
        .all()
    )
    assert len(records) == 1
    assert records[0][0] == "REJECTED"
    records = (
        db.session
        .query(RawExternalSeqrun.status)
        .filter(
            RawExternalSeqrun.raw_external_seqrun_igf_id=="IIJJKKLL"
        )
        .all()
    )
    assert len(records) == 1
    assert records[0][0] == "UNKNOWN"


def test_action_add_raw_external_seqrun(
    db
):
    platform1 = Platform(
        platform_igf_id="AABBCCDD",
        model_name="NOVASEQ6000",
        vendor_name="ILLUMINA",
        software_name="RTA"
    )
    raw_run1 = RawExternalSeqrun(
        raw_external_seqrun_igf_id="260124_AABBCCDD_100_EEFFGGHH110",
        status="UNKNOWN"
    )
    raw_run2 = RawExternalSeqrun(
        raw_external_seqrun_igf_id="EEFFGGHH",
        status="UNKNOWN"
    )
    raw_run3 = RawExternalSeqrun(
        raw_external_seqrun_igf_id="260124_AABBCCDD_101_EEFFGGHH110",
        status="UNKNOWN"
    )
    raw_run4 = RawExternalSeqrun(
        raw_external_seqrun_igf_id="EEFFGGHHI",
        status="UNKNOWN"
    )
    db.session.add(platform1)
    db.session.add(raw_run1)
    db.session.add(raw_run2)
    db.session.add(raw_run3)
    db.session.add(raw_run4)
    db.session.flush()
    db.session.commit()
    with patch.dict('os.environ', {'AIRFLOW_CONF_FILE': 'test_conf'}):
        with patch("app.external_raw_seqrun_view.get_airflow_dag_id",
                    return_values="test_dag"):
            with patch("app.external_raw_seqrun_view.async_trigger_airflow_pipeline",
                        return_values={"AABBCC": "done"}):
                run_list1, errors1 = action_add_raw_external_seqrun(
                    raw_run1
                )
                run_list2, errors2 = action_add_raw_external_seqrun(
                    raw_run2
                )
                run_list3, errors3 = action_add_raw_external_seqrun(
                    [raw_run3]
                )
                run_list4, errors4 = action_add_raw_external_seqrun(
                    [raw_run4]
                )
    assert len(run_list1) == 1
    assert len(errors1) == 0
    assert len(run_list2) == 0
    assert len(errors2) == 1
    assert len(run_list3) == 1
    assert len(errors3) == 0
    assert len(run_list4) == 0
    assert len(errors4) == 1