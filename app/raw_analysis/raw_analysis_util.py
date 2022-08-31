import os
import json
from ..models import RawAnalysis
from .. import db
from typing import Union
from jsonschema import Draft4Validator, ValidationError

def validate_analysis_json(
        analysis_json_data: list,
        schema_json_file: str=os.path.join(os.path.dirname(__file__), 'analysis_validation.json')) \
            -> list:
    try:
        with open(schema_json_file, 'r') as fp:
            schema_json_data = json.load(fp)
        analysis_validator = \
            Draft4Validator(schema_json_data)
        validation_errors = \
            sorted(
                analysis_validator.\
                    iter_errors(analysis_json_data),
                key=lambda e: e.path)
        error_list = list()
        for err in validation_errors:
            if isinstance(err, str):
                error_list.append(err)
            else:
                if len(err.schema_path) > 2:
                    error_list.append(
                        f"{err.schema_path[2]}: {err.message}")
                else:
                    error_list.append(
                        err.message)
        return error_list
    except Exception as e:
        print(e)
        return False