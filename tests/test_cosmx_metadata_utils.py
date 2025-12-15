from app.cosmx_metadata.cosmx_metadata_utils import (
    check_project_data_validation,
    check_user_data_validation,
    raw_user_query,
    fetch_raw_cosmx_builder_data,
    check_metadata_on_loader_table,
    validate_raw_cosmx_metadata,
    add_failed_reports_to_builder_table,
    build_metadata_and_load_raw_metadata_for_pipeline,
    validate_raw_cosmx_metadata_and_add_to_loader_table
)
from app.models import (
    RawIgfUser,
    RawCosMxMetadataBuilder,
    RawCosMxMetadataModel
)

def test_check_project_data_validation():
    project_igf_id = "IGFQ001"
    err_list = check_project_data_validation(
        project_igf_id=project_igf_id
    )
    assert len(err_list) == 0
    project_igf_id = "IGFQ"
    err_list = check_project_data_validation(
        project_igf_id=project_igf_id
    )
    assert len(err_list) == 1
    project_igf_id = "IGFQ(a)"
    err_list = check_project_data_validation(
        project_igf_id=project_igf_id
    )
    assert len(err_list) == 1


def test_check_user_data_validation():
    user_data1 = {
        "name": "Bob Jones",
        "email_id": "bob@example.com",
        "username": "bob123"
    }
    err_list = check_user_data_validation(
        user_info_dictionary=user_data1
    )
    assert len(err_list) == 0
    user_data2 = {
        "name": "Bob",
        "email_id": "bob@example.com",
        "username": "bob123"
    }
    err_list = check_user_data_validation(
        user_info_dictionary=user_data2
    )
    assert len(err_list) == 1
    user_data3 = {
        "name": "Bob Jones",
        "email_id": "bob@example.com",
        "username": "bob"
    }
    err_list = check_user_data_validation(
        user_info_dictionary=user_data3
    )
    assert len(err_list) == 1
    user_data4 = {
        "name": "Bob Jones",
        "email_id": "bob@example.com"
    }
    err_list = check_user_data_validation(
        user_info_dictionary=user_data4
    )
    assert len(err_list) == 0


def test_raw_user_query(db):
    user1 = RawIgfUser(
        user_id=1,
        name="test1",
        email_id="test1"
    )
    user2 = RawIgfUser(
        user_id=2,
        name="test2",
        email_id="test2"
    )
    user3 = RawIgfUser(
        user_id=3,
        name="test3",
        email_id="test3",
        status="WITHDRAWN"
    )
    try:
        db.session.add(user1)
        db.session.add(user2)
        db.session.add(user3)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    records = raw_user_query()
    assert records is not None
    assert len(records) == 2
    user_ids = [entry.user_id for entry in records]
    assert 3 not in user_ids
    assert 2 in user_ids

def test_fetch_raw_cosmx_builder_data(db):
    raw_user1 = RawIgfUser(
        user_id=1,
        name="test1",
        email_id="test1"
    )
    raw_data1 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=1,
        cosmx_metadata_tag="test_prj_1",
        name="My Name",
        email_id="my@email.com",
    )
    raw_data2 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=2,
        cosmx_metadata_tag="test_prj_2",
        raw_user_id=raw_user1.user_id
    )
    try:
        db.session.add(raw_user1)
        db.session.add(raw_data1)
        db.session.add(raw_data2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    data = fetch_raw_cosmx_builder_data(
        raw_cosmx_id=raw_data1.raw_cosmx_metadata_builder_id
    )
    assert data is not None
    assert isinstance(data, RawCosMxMetadataBuilder)
    assert data.cosmx_metadata_tag == "test_prj_1"
    data = fetch_raw_cosmx_builder_data(
        raw_cosmx_id=raw_data2.raw_cosmx_metadata_builder_id
    )
    assert data is not None
    assert isinstance(data, RawCosMxMetadataBuilder)
    assert data.cosmx_metadata_tag == "test_prj_2"
    assert data.raw_user_id == 1
    data = fetch_raw_cosmx_builder_data(
        raw_cosmx_id=3
    )
    assert data is None

def test_check_metadata_on_loader_table(db):
    raw_metadata1 = RawCosMxMetadataModel(
        cosmx_metadata_tag="test1"
    )
    try:
        db.session.add(raw_metadata1)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
    erros = check_metadata_on_loader_table(
        cosmx_metadata_tag="test1"
    )
    assert len(erros) == 1
    erros = check_metadata_on_loader_table(
        cosmx_metadata_tag="test2"
    )
    assert len(erros) == 0

def test_add_failed_reports_to_builder_table(db):
    raw_data1 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=1,
        cosmx_metadata_tag="test_prj_1",
        name="My Name",
        email_id="my@email.com",
    )
    try:
        db.session.add(raw_data1)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    add_failed_reports_to_builder_table(
        raw_cosmx_id=raw_data1.raw_cosmx_metadata_builder_id,
        error_list=["A", "B"]
    )
    record = (
        db.session
        .query(RawCosMxMetadataBuilder)
        .filter(
            RawCosMxMetadataBuilder.raw_cosmx_metadata_builder_id
            == raw_data1.raw_cosmx_metadata_builder_id
        )
        .one_or_none()
    )
    assert record is not None
    assert record.status == "FAILED"
    assert record.report == "\n".join(["A", "B"])
    add_failed_reports_to_builder_table(
        raw_cosmx_id=100,
        error_list=["A", "B"]
    )

def test_build_metadata_and_load_raw_metadata_for_pipeline(db):
    raw_data1 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=1,
        cosmx_metadata_tag="test_prj_1",
        name="My Name",
        email_id="my@email.com",
    )
    raw_user1 = RawIgfUser(
        user_id=1,
        name="test1",
        email_id="test1"
    )
    raw_data2 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=2,
        cosmx_metadata_tag="test_prj_2",
        raw_user_id=raw_user1.user_id
    )
    try:
        db.session.add(raw_data1)
        db.session.add(raw_user1)
        db.session.add(raw_data2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    build_metadata_and_load_raw_metadata_for_pipeline(
        raw_cosmx_id=raw_data1.raw_cosmx_metadata_builder_id
    )
    record = (
        db.session.query(RawCosMxMetadataModel)
        .filter(
            RawCosMxMetadataModel.cosmx_metadata_tag
            == raw_data1.cosmx_metadata_tag
        )
        .one_or_none()
    )
    assert record is not None
    assert record.status == 'READY'
    assert "project_igf_id,name,email_id,deliverable" in record.formatted_csv_data
    assert "test_prj_1,My Name,my@email.com,COSMX" in record.formatted_csv_data
    metadata_id = build_metadata_and_load_raw_metadata_for_pipeline(
        raw_cosmx_id=raw_data2.raw_cosmx_metadata_builder_id
    )
    record = (
        db.session.query(RawCosMxMetadataModel)
        .filter(
            RawCosMxMetadataModel.cosmx_metadata_tag
            == raw_data2.cosmx_metadata_tag
        )
        .one_or_none()
    )
    assert record is not None
    assert record.status == 'READY'
    assert record.raw_cosmx_metadata_id == metadata_id
    assert "project_igf_id,name,email_id,COSMX" in record.formatted_csv_data
    assert "test_prj_2,test1,test1,deliverable" in record.formatted_csv_data

def test_validate_raw_cosmx_metadata(db):
    raw_data1 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=1,
        cosmx_metadata_tag="test_prj_1",
        name="My Name",
        email_id="my@email.com",
    )
    raw_data2 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=2,
        cosmx_metadata_tag="test",
        name="My",
        email_id="myemail.com",
    )
    try:
        db.session.add(raw_data1)
        db.session.add(raw_data2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    error_list = validate_raw_cosmx_metadata(
        raw_cosmx_id=raw_data1.raw_cosmx_metadata_builder_id
    )
    assert len(error_list) == 0
    error_list = validate_raw_cosmx_metadata(
        raw_cosmx_id=raw_data2.raw_cosmx_metadata_builder_id
    )
    assert len(error_list) == 3

def test_validate_raw_cosmx_metadata_and_add_to_loader_table(db):
    raw_data1 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=1,
        cosmx_metadata_tag="test_prj_1",
        name="My Name",
        email_id="my@email.com",
    )
    raw_data2 = RawCosMxMetadataBuilder(
        raw_cosmx_metadata_builder_id=2,
        cosmx_metadata_tag="test",
        name="My",
        email_id="myemail.com",
    )
    try:
        db.session.add(raw_data1)
        db.session.add(raw_data2)
        db.session.flush()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    status, error_list, metadata_id = validate_raw_cosmx_metadata_and_add_to_loader_table(
        raw_cosmx_id=raw_data1.raw_cosmx_metadata_builder_id
    )
    assert status == "VALIDATED"
    assert len(error_list) == 0
    record = (
        db.session.query(RawCosMxMetadataModel)
        .filter(
            RawCosMxMetadataModel.cosmx_metadata_tag
            == raw_data1.cosmx_metadata_tag
        )
        .one_or_none()
    )
    assert record is not None
    assert record.status == 'READY'
    assert record.raw_cosmx_metadata_id == metadata_id
    status, error_list, metadata_id = validate_raw_cosmx_metadata_and_add_to_loader_table(
        raw_cosmx_id=raw_data2.raw_cosmx_metadata_builder_id
    )
    assert status == "FAILED"
    assert metadata_id is None
    assert len(error_list) > 0
    record = (
        db.session.query(RawCosMxMetadataModel)
        .filter(
            RawCosMxMetadataModel.cosmx_metadata_tag
            == raw_data2.cosmx_metadata_tag
        )
        .one_or_none()
    )
    assert record is None