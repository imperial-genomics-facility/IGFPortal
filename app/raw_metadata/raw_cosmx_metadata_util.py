from multiprocessing.sharedctypes import Value
from numpy import isin
import pandas as pd
import os, json, re, tempfile, logging, typing
from typing import Tuple
from jsonschema import Draft4Validator, ValidationError
from .. import db
from ..models import RawCosMxMetadataModel, Project
from ..metadata.metadata_util import (
    check_for_projects_in_metadata_db,
    check_user_name_and_email_in_metadata_db)

def _run_metadata_json_validation(
    metadata_file: str,
    schema_json: str) -> list:
    try:
        if not os.path.exists(metadata_file) or \
           not os.path.exists(schema_json):
           raise IOError("Input file error")
        error_list = list()
        with open(schema_json,'r') as jf:
            schema = json.load(jf)
        metadata_validator = Draft4Validator(schema)
        metadata_json_fields = list(schema['items']['properties'].keys())
        metadata_df = pd.read_csv(metadata_file)
        metadata_df.fillna('', inplace=True)
        for header_name in metadata_df.columns:
            if header_name not in metadata_json_fields:
                error_list.append(f"Unexpected column {header_name} found")
        json_data = \
            metadata_df.\
                to_dict(orient='records')
        validation_errors = \
            sorted(
                metadata_validator.iter_errors(json_data),
                key=lambda e: e.path)
        for err in validation_errors:
            if isinstance(err, str):
                error_list.append(err)
            else:
                if len(err.schema_path) > 2:
                    error_list.append(
                        f"{err.schema_path[2]}: {err.message}")
                else:
                    error_list.append(
                        f"{err.message}")
        return error_list
    except Exception as e:
        raise ValueError(
            f"Failed to run json validation, error: {e}")


def _set_metadata_validation_status(
    raw_cosmx_metadata_id: int,
    status: str,
    report: str='') -> None:
    try:
        if status.upper() == 'VALIDATED':
            try:
                db.session.\
                    query(RawCosMxMetadataModel).\
                    filter(RawCosMxMetadataModel.raw_cosmx_metadata_id==raw_cosmx_metadata_id).\
                    update({
                        'status': 'VALIDATED',
                        'report': ''})
                db.session.commit()
            except:
                db.session.rollback()
                raise
        elif status.upper() == 'FAILED':
            try:
                db.session.\
                    query(RawCosMxMetadataModel).\
                    filter(RawCosMxMetadataModel.raw_cosmx_metadata_id==raw_cosmx_metadata_id).\
                    update({
                        'status': 'FAILED',
                        'report': report})
                db.session.commit()
            except:
                db.session.rollback()
                raise
        else:
            db.session.\
                query(RawCosMxMetadataModel).\
                filter(RawCosMxMetadataModel.raw_cosmx_metadata_id==raw_cosmx_metadata_id).\
                update({
                    'status': 'UNKNOWN'})
    except Exception as e:
        raise ValueError(
            f"Failed to set metadata status for id {raw_cosmx_metadata_id}, error: {e}")



def _check_project_and_user_details(
        metadata_file: str,
        project_column: str='project_igf_id',
        name_column: str='name',
        email_column: str='email_id') -> list:
    try:
        errors = list()
        df = pd.read_csv(metadata_file)
        if not project_column in df.columns or \
           not name_column in df.columns or \
           not email_column in df.columns:
            errors.append(
                f"Column {project_column} or {name_column} or {email_column} not found in metadata file")
            return errors
        project_id_list = \
            df[project_column].\
                drop_duplicates().\
                to_list()
        user_name_list = \
            df[[name_column, email_column]].\
                drop_duplicates().\
                to_dict(orient='records')
        _, project_errors = \
            check_for_projects_in_metadata_db(
                project_list=project_id_list,
                flag_existing_project=True)
        if len(project_errors) > 0:
            errors.extend(project_errors)
        user_errors = \
            check_user_name_and_email_in_metadata_db(
                name_email_list=user_name_list,
                name_column=name_column,
                email_column=email_column,
                check_missing=False)
        if len(user_errors) > 0:
            errors.extend(user_errors)
        return errors
    except Exception as e:
        raise ValueError(
            f"Failed to check project and user details, error: {e}")


def validate_raw_cosmx_metadata_and_set_db_status(
        raw_cosmx_metadata_id: int,
        schema_json: str = os.path.join(os.path.dirname(__file__), 'cosmx_metadata_validation.json')) \
            -> str:
    """
    Validate the raw metadata and set the status in the database.
    """
    try:
        error_list = list()
        raw_cosmx_metadata = \
            db.session.\
                query(RawCosMxMetadataModel).\
                filter(RawCosMxMetadataModel.raw_cosmx_metadata_id==raw_cosmx_metadata_id).\
                one_or_none()
        if raw_cosmx_metadata is None:
            raise ValueError(
                f"No metadata entry found for id {raw_cosmx_metadata_id}")
        csv_data = raw_cosmx_metadata.formatted_csv_data
        if csv_data is None or csv_data == "":
            raise ValueError(
                f"No formatted csv data found for id {raw_cosmx_metadata_id}")
        with tempfile.TemporaryDirectory() as temp_dir:
            metadata_file = os.path.join(temp_dir, 'metadata.csv')
            with open(metadata_file, 'w') as fp:
                fp.write(csv_data)
            try:
                _ = pd.read_csv(metadata_file)
            except:
                error_list.append('Not CSV input file')
                _set_metadata_validation_status(
                    raw_cosmx_metadata_id=raw_cosmx_metadata_id,
                    status='FAILED',
                    report='\n'.join(error_list))
                return 'FAILED'
            validation_errors = \
                _run_metadata_json_validation(
                    metadata_file=metadata_file,
                    schema_json=schema_json)
            if len(validation_errors) > 0:
                error_list.\
                    extend(validation_errors)
            project_check_errors = \
                _check_project_and_user_details(
                    metadata_file)
            if len(project_check_errors) > 0:
                error_list.\
                    extend(project_check_errors)
            if len(error_list) > 0:
                error_list = \
                    [f"{i+1}, {e}"
                        for i,e in enumerate(error_list)]
                _set_metadata_validation_status(
                    raw_cosmx_metadata_id=raw_cosmx_metadata_id,
                    status='FAILED',
                    report='\n'.join(error_list))
                return 'FAILED'
            else:
                _set_metadata_validation_status(
                    raw_cosmx_metadata_id=raw_cosmx_metadata_id,
                    report='',
                    status='VALIDATED')
                return 'VALIDATED'
    except Exception as e:
        raise ValueError(
            f"Failed to get metadata for id {raw_cosmx_metadata_id}, error: {e}")


def download_ready_cosmx_metadata() -> dict:
    """
    Download the ready metadata from the database.

    :return: dict
        A dictionary containing the metadata tag and formatted csv data.
    """
    try:
        results = \
            db.session.\
                query(
                    RawCosMxMetadataModel.cosmx_metadata_tag,
                    RawCosMxMetadataModel.formatted_csv_data).\
                    filter(RawCosMxMetadataModel.status=='VALIDATED').\
                    all()
        if len(results)==0:
            return {}
        else:
            data = dict()
            for entry in results:
                data.update({entry[0]: entry[1]})
            return data
    except Exception as e:
        raise ValueError(
            f"Failed to download ready metadata, error: {e}")