import os, unittest
import pandas as pd
from app.models import (
    RawCosMxMetadataModel,
    Project,
    IgfUser)
from app.raw_metadata.raw_cosmx_metadata_util import (
    _run_metadata_json_validation,
    _set_metadata_validation_status,
    validate_raw_cosmx_metadata_and_set_db_status)

def test_run_metadata_json_validation(tmp_path):
    schema_json = "app/raw_metadata/cosmx_metadata_validation.json"
    metadata_list = [
        {"project_id": 1}]
    metadata_file = \
        os.path.join(tmp_path, 'raw_metadata.csv')
    pd.DataFrame(
        metadata_list).\
            to_csv(
                metadata_file,
                index=False)
    error_list = \
        _run_metadata_json_validation(
            metadata_file=metadata_file,
            schema_json=schema_json)
    assert len(error_list) == 4
    assert "Unexpected column project_id found" in error_list
    metadata_list = [
        {"project_igf_id": "IGFQA-1234",
         "name": "test user",
         "email_id": "a@d.com",
         "username": "test"}]
    metadata_file = \
        os.path.join(tmp_path, 'raw_metadata.csv')
    pd.DataFrame(
        metadata_list).\
            to_csv(
                metadata_file,
                index=False)
    error_list = \
        _run_metadata_json_validation(
            metadata_file=metadata_file,
            schema_json=schema_json)
    assert len(error_list) == 0
    metadata_list = [
        {"project_igf_id": "IGFQA-1234",
         "name": "test user",
         "email_id": "a-d.com",
         "username": "test"}]
    metadata_file = \
        os.path.join(tmp_path, 'raw_metadata.csv')
    pd.DataFrame(
        metadata_list).\
            to_csv(
                metadata_file,
                index=False)
    error_list = \
        _run_metadata_json_validation(
            metadata_file=metadata_file,
            schema_json=schema_json)
    assert len(error_list) == 1


def test_set_metadata_validation_status(db):
        metadata = \
            RawCosMxMetadataModel(
                raw_cosmx_metadata_id=1,
                cosmx_metadata_tag='test1',
                formatted_csv_data='formatted',
                report='')
        try:
            db.session.add(metadata)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        result = \
            db.session.\
                query(RawCosMxMetadataModel).\
                filter(RawCosMxMetadataModel.raw_cosmx_metadata_id==1).\
                one_or_none()
        assert result is not None
        assert result.cosmx_metadata_tag == 'test1'
        assert result.status == 'UNKNOWN'
        _set_metadata_validation_status(
            raw_cosmx_metadata_id=1,
            status='failed',
            report='error')
        result = \
            db.session.\
                query(RawCosMxMetadataModel).\
                filter(RawCosMxMetadataModel.raw_cosmx_metadata_id==1).\
                one_or_none()
        assert result is not None
        assert result.cosmx_metadata_tag, 'test1'
        assert result.status == 'FAILED'
        _set_metadata_validation_status(
            raw_cosmx_metadata_id=1,
            status='validated')
        result = \
            db.session.\
                query(RawCosMxMetadataModel).\
                filter(RawCosMxMetadataModel.raw_cosmx_metadata_id==1).\
                one_or_none()
        assert result is not None
        assert result.cosmx_metadata_tag == 'test1'
        assert result.status == 'VALIDATED'