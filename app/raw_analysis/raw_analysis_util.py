from ..models import RawAnalysis
from .. import db
from typing import Union
from jsonschema import Draft4Validator, ValidationError

def validate_analysis_json(
        analysis_json_data: list,
        schema_json_data: list) \
            -> Union[list, None]:
    try:
        analysis_validator = \
            Draft4Validator(schema_json_data)
        validation_errors = \
            sorted(
                analysis_validator.iter_errors(analysis_json_data),
                key=lambda e: e.path)
        return validation_errors
    except Exception as e:
        print(e)
        return False