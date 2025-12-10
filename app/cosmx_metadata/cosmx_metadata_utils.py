from pydantic import (
    BaseModel,
    EmailStr,
    Field,
    field_validator,
    ValidationError
)
from typing import Optional
import re
from app import db
from app.models import (
    RawIgfUser,
    RawCosMxMetadataBuilder,
    RawCosMxMetadataModel
)

class User(BaseModel):
    name: str = Field(
        min_length=5,
        description="User's full name (minimum 5 characters)"
    )
    email: EmailStr = Field(
        description="User's email address"
    )
    username: Optional[str] = Field(
        None,
        min_length=5,
        description="Optional username (a-z, 0-9, ., -), minimum 5 characters"
    )

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            if not re.match(r'^[a-z0-9.-]+$', v):
                raise ValueError('Username must only contain letters (a-z), numbers (0-9), dots (.), and hyphens (-)')
        return v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z-\s]+$', v):
                raise ValueError('Name must only contain letters (a-z, A-Z), white spaces and hyphens (-)')
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
            f"Failed to check validation error, error: {e}")


def raw_user_query():
    try:
        results = db.session.query(
            RawIgfUser
        ).filter(
            RawIgfUser.status=='ACTIVE'
        ).order_by(
            RawIgfUser.user_id.desc()
        ).all()
        return results
    except Exception as e:
        raise ValueError(
            f"Failed to get project list, error: {e}")

def fetch_raw_cosmx_builder_data(
    raw_cosmx_id: int
) -> RawCosMxMetadataBuilder|None:
    try:
        entry = (
            db.session.query(
                RawCosMxMetadataBuilder
            )
            .filter(
                RawCosMxMetadataBuilder.raw_cosmx_metadata_builder_id == raw_cosmx_id
            ).
            one_or_none()
        )
        return entry
    except Exception as e:
        raise ValueError(
            f"Failed to fetch raw data from builder table, error: {e}"
        )


def validate_raw_cosmx_metadata_and_add_to_loader_table(
        raw_cosmx_id: int,
        failed_status: str = 'FAILED',
        validated_status: str = 'VALIDATED',
        ready_status: str = 'READY'
) -> str:
    try:
        status = failed_status
        ## step 1: fetch raw cosmx metadata
        ## step 2: check if raw metadata already present on the loader table
        ## step 3: check for required info
        ## step 4: validate project info
        ## step 5: validate new user info
        ## step 6: add validation error to the reports
        ## step 7: add new records to loader table
        ## step 8: trigger pipeline
        return status
    except Exception as e:
        raise ValueError(
            f"Failed to validate raw cosmx metadata, error: {e}"
        )