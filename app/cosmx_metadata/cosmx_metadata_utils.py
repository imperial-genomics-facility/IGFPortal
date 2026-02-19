from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    ValidationError
)
from sqlalchemy import or_
from typing import Literal
import re
import pandas as pd
from app import db
from app.models import (
    IgfUser,
    Project,
    RawIgfUser,
    RawCosMxMetadataBuilder,
    RawCosMxMetadataModel
)

class Project_data(BaseModel):
    project_igf_id: str = Field(
        min_length=5,
        max_length=70,
        description="Project_igf_id (min 5 and max 70 characters)"
    )

    @field_validator('project_igf_id')
    @classmethod
    def validate_project_igf_id(cls, v):
        if v is not None:
            if not re.match(r'^[A-Za-z0-9_]+$', v):
                raise ValueError(
                    'project_igf_id must only contain letters (A-Z , a-z), '
                    + 'numbers (0-9) and underscore (_)'
                )
        return v

def check_project_data_validation(
    project_igf_id: str,
    project_igf_id_tag: str = 'project_igf_id'
) -> list:
    try:
        error_list = list()
        try:
            _ = Project_data(**{project_igf_id_tag: project_igf_id})
        except ValidationError as e:
            for error in e.errors():
                error_list.append(
                    f"Project field: {error['loc']}, Error: {error['msg']}"
                )
        return error_list
    except Exception as e:
        raise ValueError(
            f"Failed to check validation error, error: {e}")


class User(BaseModel):
    name: str = Field(
        min_length=5,
        description="User's full name (minimum 5 characters)"
    )
    email_id: EmailStr = Field(
        description="User's email address"
    )
    username: str = Field(
        min_length=5,
        description="Username (a-z, 0-9, ., -), minimum 5 characters"
    )
    category: Literal["HPC_USER", "NON_HPC_USER", ""] = Field(
        default=None,
        description="User category: 'HPC_USER', 'NON_HPC_USER', or ''"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            if not re.match(r'^[a-z0-9.-]+$', v):
                raise ValueError(
                    'Username must only contain letters (a-z), numbers (0-9), '
                    + 'dots (.), and hyphens (-)'
                )
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z-\s]+$', v):
                raise ValueError(
                    'Name must only contain letters (a-z, A-Z), '
                    + 'white spaces and hyphens (-)'
                )
        return v

def check_user_data_validation(
    user_info_dictionary: dict[str, str]
    ) -> list:
    try:
        error_list = list()
        try:
            _ = User(**user_info_dictionary)
        except ValidationError as e:
            for error in e.errors():
                error_list.append(
                    f"User field: {error['loc']}, Error: {error['msg']}"
                )
        return error_list
    except Exception as e:
        raise ValueError(
            "Failed to check validation error, error: "
            + str(e)
        )


def raw_user_query():
    try:
        results = (
            db.session
            .query(RawIgfUser)
            .filter(
                RawIgfUser.status=='ACTIVE'
            )
            .order_by(
                RawIgfUser.user_id.desc()
            )
            .all()
        )
        return results
    except Exception as e:
        raise ValueError(
            "Failed to get project list, error: "
            + str(e)
        )


def fetch_raw_cosmx_builder_data(
    raw_cosmx_id: int
) -> RawCosMxMetadataBuilder|None:
    try:
        entry = (
            db.session
            .query(RawCosMxMetadataBuilder)
            .filter(
                RawCosMxMetadataBuilder.raw_cosmx_metadata_builder_id
                == raw_cosmx_id
            )
            .one_or_none()
        )
        return entry
    except Exception as e:
        raise ValueError(
            "Failed to fetch raw data from builder table, error: "
            + str(e)
        )

def check_metadata_conflict(
    raw_cosmx_data: RawCosMxMetadataBuilder
) -> list[str]:
    try:
        error_list = list()
        project_record = (
            db.session.query(Project)
            .filter(
                Project.project_igf_id
                == raw_cosmx_data.cosmx_metadata_tag
            )
            .all()
        )
        if len(project_record) > 0:
            error_list.append(
                f"Project {raw_cosmx_data.cosmx_metadata_tag} already in db!"
            )
        if raw_cosmx_data.raw_user_id is None:
            user_record = (
                db.session.query(IgfUser)
                .filter(
                    or_(
                        IgfUser.name == raw_cosmx_data.name,
                        IgfUser.email_id == raw_cosmx_data.email_id,
                        IgfUser.username == raw_cosmx_data.username
                    )
                )
                .all()
            )
            if len(user_record) > 0:
                error_list.append(
                    f"User {raw_cosmx_data.email_id} already in db!"
                )
        return error_list
    except Exception as e:
        raise ValueError(
            "Failed to check new metadata with existing records, error: "
            + str(e)
        )

def check_required_raw_cosmx_metadata(
    raw_cosmx_data: RawCosMxMetadataBuilder,
    hpc_user_category: str = "HPC_USER"
) -> list[str]:
    try:
        errors = list()
        ## check project name
        errors = check_project_data_validation(
            project_igf_id=raw_cosmx_data.cosmx_metadata_tag
        )
        if (
            raw_cosmx_data.email_id is None
            and raw_cosmx_data.raw_user_id is None
        ):
            errors.append(
                "Enter new user or select existing user info"
            )
        if raw_cosmx_data.raw_user_id is None:
            user_info_dictionary = {
                "name": raw_cosmx_data.name,
                "email_id": raw_cosmx_data.email_id,
                "username": raw_cosmx_data.username
            }
            if raw_cosmx_data.username is not None:
                user_info_dictionary.update({
                    "category": hpc_user_category
                })
            new_user_errors = check_user_data_validation(
                user_info_dictionary=user_info_dictionary
            )
            errors.extend(
                new_user_errors
            )
        return errors
    except Exception as e:
        raise ValueError(
            "Failed to check required raw metadata on builder table, error: "
            + str(e)
        )


def check_metadata_on_loader_table(
    cosmx_metadata_tag: str
) -> list[str]:
    try:
        error_list = list()
        record = (
            db.session
            .query(RawCosMxMetadataModel)
            .filter(
                RawCosMxMetadataModel.cosmx_metadata_tag
                == cosmx_metadata_tag
            )
            .one_or_none()
        )
        if record is not None:
            error_list.append(
                f"{cosmx_metadata_tag} is already present in the database"
            )
        return error_list
    except Exception as e:
        raise ValueError(
            "Failed to check raw data on loader table, error: "
            + str(e)
        )


def validate_raw_cosmx_metadata(
    raw_cosmx_id: int
) -> list[str]:
    try:
        ## step 1: fetch raw cosmx metadata
        raw_metadata_entry = fetch_raw_cosmx_builder_data(
            raw_cosmx_id=raw_cosmx_id
        )
        if raw_metadata_entry is None:
            error_list = [
                f"No entry for raw metadata id {raw_metadata_entry} is present"
            ]
            return error_list
        ## step 2:
        ## * check for required info
        ## * validate project info
        ## * validate new user info
        error_list = list()
        errors = check_required_raw_cosmx_metadata(
            raw_cosmx_data=raw_metadata_entry
        )
        if len(errors) > 0:
            error_list.extend(
                errors
            )
        ## step 3: check if raw metadata already present on the loader table
        errors = check_metadata_on_loader_table(
            cosmx_metadata_tag=raw_metadata_entry.cosmx_metadata_tag
        )
        if len(errors) > 0:
            error_list.extend(
                errors
            )
        ## step 4: check for metadata conflict
        errors = check_metadata_conflict(
            raw_cosmx_data=raw_metadata_entry
        )
        if len(errors) > 0:
            error_list.extend(
                errors
            )
        return error_list
    except Exception as e:
        raise ValueError(
            "Failed to check raw data on loader table, error: "
            + str(e)
        )


def add_failed_reports_to_builder_table(
    raw_cosmx_id: int,
    error_list: list[str],
    failed_status: str = 'FAILED'
) -> None:
    try:
        raw_metadata_entry = fetch_raw_cosmx_builder_data(
            raw_cosmx_id=raw_cosmx_id
        )
        if (
            raw_metadata_entry is not None
            and len(error_list) > 0
        ):
            try:
                (
                    db.session
                    .query(RawCosMxMetadataBuilder)
                    .filter(
                        RawCosMxMetadataBuilder.raw_cosmx_metadata_builder_id
                        == raw_cosmx_id
                    )
                    .update({
                        "report": "\n".join(error_list),
                        "status": failed_status
                    })
                )
                db.session.commit()
            except Exception as e:
                db.session.rollback()
                raise ValueError(
                    "Failed to update failed reports, error: "
                    + str(e)
                )
    except Exception as e:
        raise ValueError(
            "Failed to check raw data on loader table, error: "
            + str(e)
        )


def build_metadata_and_load_raw_metadata_for_pipeline(
    raw_cosmx_id: int,
    ready_status: str = 'READY',
    validated_status: str = 'VALIDATED',
    project_igf_id_tag: str = "project_igf_id",
    name_tag: str = "name",
    email_id_tag: str = "email_id",
    username_tag: str = "username",
    deliverable_tag: str = "deliverable",
    deliverable_type: str = "COSMX",
    categoty_tag: str = "category",
    category_type: str = "HPC_USER"
) -> int|None:
    try:
        raw_cosmx_metadata_id = None
        ## step 1: fetch raw cosmx metadata
        raw_metadata_entry = fetch_raw_cosmx_builder_data(
            raw_cosmx_id=raw_cosmx_id
        )
        if raw_metadata_entry is None:
            raise ValueError(
                f"No data found on builder table for {raw_cosmx_id}"
            )
        metadata = dict()
        ## assuming its already validated
        if raw_metadata_entry.raw_user_id is None:
            metadata = {
                project_igf_id_tag: raw_metadata_entry.cosmx_metadata_tag,
                name_tag: raw_metadata_entry.name,
                email_id_tag: raw_metadata_entry.email_id,
                username_tag: raw_metadata_entry.username,
                deliverable_tag: deliverable_type,
                categoty_tag: category_type
            }
        else:
            raw_user_record = (
                db.session
                .query(RawIgfUser)
                .filter(
                    RawIgfUser.user_id==raw_metadata_entry.raw_user_id
                )
                .one_or_none()
            )
            if raw_user_record is None:
                raise ValueError(
                    "No entry for user "
                    + f"{raw_metadata_entry.raw_user_id} found in db"
                )
            metadata = {
                project_igf_id_tag: raw_metadata_entry.cosmx_metadata_tag,
                name_tag: raw_user_record.name,
                email_id_tag: raw_user_record.email_id,
                username_tag: raw_user_record.username,
                deliverable_tag: deliverable_type,
                categoty_tag: category_type
            }
        ## step 2: load data and change status
        try:
            csv_data = (
                pd.DataFrame([metadata])
                .to_csv(index=False)
            )
            ## update loader table
            raw_metadata = RawCosMxMetadataModel(
                cosmx_metadata_tag=raw_metadata_entry.cosmx_metadata_tag,
                formatted_csv_data=csv_data,
                status=ready_status
            )
            db.session.add(raw_metadata)
            db.session.flush()
            ## change status at builder table
            (
                db.session
                .query(RawCosMxMetadataBuilder)
                .filter(
                    RawCosMxMetadataBuilder.raw_cosmx_metadata_builder_id
                    == raw_cosmx_id
                )
                .update({
                    "report": "",
                    "status": validated_status
                })
            )
            db.session.commit()
            raw_cosmx_metadata_id = raw_metadata.raw_cosmx_metadata_id
        except Exception as e:
            db.session.rollback()
            raise ValueError(
                "Failed to transfer data to loader table. error: "
                + str(e)
            )
        return raw_cosmx_metadata_id
    except Exception as e:
        raise ValueError(
            "Failed to build and load raw metadata for loader table: error: "
            + str(e)
        )

def validate_raw_cosmx_metadata_and_add_to_loader_table(
    raw_cosmx_id: int,
    failed_status: str = 'FAILED',
    validated_status: str = 'VALIDATED',
    ready_status: str = 'READY'
) -> tuple[str, list[str], int|None]:
    try:
        error_list = list()
        ## step 1: get validation errors
        error_list = validate_raw_cosmx_metadata(
            raw_cosmx_id=raw_cosmx_id
        )
        if len(error_list) > 0:
            ## step 2: add validation error to the reports
            add_failed_reports_to_builder_table(
                raw_cosmx_id=raw_cosmx_id,
                error_list=error_list,
                failed_status=failed_status
            )
            return failed_status, error_list, None
        else:
            ## step 3: add new records to loader table
            metadata_id = build_metadata_and_load_raw_metadata_for_pipeline(
                raw_cosmx_id=raw_cosmx_id,
                ready_status=ready_status,
                validated_status=validated_status
            )
            return validated_status, error_list, metadata_id
    except Exception as e:
        raise ValueError(
            "Failed to validate raw cosmx metadata, error: "
            + str(e)
        )