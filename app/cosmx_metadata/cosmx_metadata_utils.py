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
    RawIgfUser
)

class User(BaseModel):
    name: str = Field(min_length=5, description="User's full name (minimum 5 characters)")
    email: EmailStr = Field(description="User's email address")
    username: Optional[str] = Field(None, min_length=5, description="Optional username (a-z, A-Z, 0-9, ., -), minimum 5 characters")

    @field_validator('username')
    @classmethod
    def validate_username(cls, v):
        if v is not None:
            if not re.match(r'^[a-zA-Z0-9.-]+$', v):
                raise ValueError('Username must only contain letters (a-z, A-Z), numbers (0-9), dots (.), and hyphens (-)')
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


def raw_user_query(db):
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