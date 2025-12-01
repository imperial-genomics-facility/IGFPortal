from typing import Tuple
import pandas as pd
from ..models import (
    Project,
    IgfUser,
    Sample)
from .. import db

def check_for_projects_in_metadata_db(
    project_list: list
    ) -> Tuple[dict, list]:
    try:
        errors = list()
        results = (
            db.session
            .query(Project.project_igf_id)
            .filter(Project.project_igf_id.in_(project_list))
            .all()
        )
        results = [i[0] for i in results]
        output = dict()
        for i in project_list:
            if i in results:
                output.update({i: True})
            else:
                output.update({i: False})
        for key, val in output.items():
            if not val:
                errors.append(
                    f"Project {key} is missing in db")
        return output, errors
    except Exception as e:
        raise ValueError(
            f"Failed to check projects in db, error: {e}")


def check_sample_and_project_ids_in_metadata_db(
    sample_project_list: list,
    check_user: bool = True,
    check_missing: bool =True
    ) -> list:
    try:
        input_sample_project_dict = dict()
        input_username_list = list()
        output_sample_project_dict = dict()
        errors = list()
        for entry in sample_project_list:
            if (
                'sample_igf_id' not in entry.keys()
                or 'project_igf_id' not in entry.keys()
            ):
               raise KeyError(
                    f"Missing sample id or project id in {entry}")
            if (
                entry.get('sample_igf_id') is not None
                and entry.get('project_igf_id') is not None
            ):
                input_sample_project_dict.update({
                    entry.get('sample_igf_id'): entry.get('project_igf_id')}
                )
            else:
                errors.append(
                    f'Missing data found in entry: {entry}'
                )
            if check_user:
                if (
                    'name' not in entry.keys()
                    or 'email_id' not in entry.keys()
                ):
                    raise KeyError(
                        f'Missing name or email id from metadata: {entry}')
                if (
                    entry.get('name') is not None
                    and entry.get('email_id') is not None
                ):
                    input_username_list.append({
                        'name': entry.get('name'),
                        'email_id': entry.get('email_id')}
                    )
                else:
                    errors.append(
                        f'Missing data found in entry: {entry}'
                    )
        if check_user:
            # check for name and email mismatch
            name_email_errors = check_user_name_and_email_in_metadata_db(
                name_email_list=input_username_list,
                check_missing=False)
            if len(name_email_errors) > 0:
                errors.extend(name_email_errors)
        results = (
            db.session
            .query(Sample.sample_igf_id, Project.project_igf_id)
            .join(Project, Project.project_id==Sample.project_id)
            .filter(Sample.sample_igf_id.in_(input_sample_project_dict.keys()))
            .all()
        )
        for entry in results:
            output_sample_project_dict.update({
                entry[0]: entry[1]}
            )
        for sample, project in input_sample_project_dict.items():
            if (
                sample not in output_sample_project_dict
                and check_missing
            ):
                errors.append(
                    f'Missing metadata for sample {sample}'
                )
            if (
                sample in output_sample_project_dict
                and project != output_sample_project_dict.get(sample)
            ):
               errors.append(
                    f"Sample {sample} is linked to project "
                    + str(output_sample_project_dict.get(sample))
                    + f" not {project}"
                )
        return errors
    except Exception as e:
        raise ValueError(
            f"Failed to check sample projects in db, error: {e}")

def get_email_ids_for_user_name(
    name_list: list
    ) -> dict:
    try:
        results = (
            db.session
            .query(IgfUser.name, IgfUser.email_id)
            .filter(IgfUser.name.in_(name_list))
            .all()
        )
        results = {
            i[0]: i[1]
            for i in results}
        return results
    except Exception as e:
        raise ValueError(
            f"Failed to fetch email ids for user name, error: {e}")


def get_names_for_user_email(
    email_list: list
    ) -> dict:
    try:
        results = (
            db.session
            .query(IgfUser.email_id, IgfUser.name)
            .filter(IgfUser.email_id.in_(email_list))
            .all()
        )
        results = {
            i[0]: i[1]
            for i in results}
        return results
    except Exception as e:
        raise ValueError(
            f"Failed to fetch name for email id, error: {e}")


def check_user_name_and_email_in_metadata_db(
    name_email_list: list,
    name_column: str = 'name',
    email_column: str = 'email_id',
    check_missing: bool = True
    ) -> list:
    try:
        for entry in name_email_list:
            if (
                entry.get(name_column) is None
                or entry.get(email_column) is None
            ):
               raise KeyError(
                   "Missing name or email id in the input list")
            df = pd.DataFrame(name_email_list)
            name_list = (
                df[name_column]
                .drop_duplicates()
                .values
                .tolist()
            )
            email_list = (
                df[email_column]
                .drop_duplicates()
                .values
                .tolist()
            )
            name_dict = get_email_ids_for_user_name(
                name_list)
            email_dict = get_names_for_user_email(
                email_list)
            errors = list()
            for entry in name_email_list:
                name = entry.get('name')
                email_id = entry.get('email_id')
                if (
                    name_dict.get(name) is None
                    and check_missing
                ):
                    errors.append(
                        f'Missing name {name} in db'
                    )
                if (
                    email_dict.get(email_id) is None
                    and check_missing
                ):
                    errors.append(
                        f'Missing email {email_id} in db'
                    )
                if (
                    name_dict.get(name) is not None
                    and email_id != name_dict.get(name)
                ):
                   errors.append(
                       f"User {name} registered with email id " 
                       + str(name_dict.get(name))
                       + f"not {email_id}"
                    )
                if (
                    email_dict.get(email_id) is not None
                    and name != email_dict.get(email_id)
                ):
                   errors.append(
                       f"Email {email_id} registered with name "
                       + str(email_dict.get(email_id))
                       + f"not {name}"
                    )
        return errors
    except Exception as e:
        raise ValueError(
            f"Failed to compate user name and email in db, error: {e}")