import os, json, typing
import pandas as pd
from ..models import Project
from ..models import IgfUser
from ..models import ProjectUser
from ..models import Project_attribute
from ..models import Sample
from ..models import Sample_attribute
from ..models import Experiment
from ..models import Experiment_attribute
from ..models import Run
from ..models import Run_attribute
from ..models import Platform
from ..models import Flowcell_barcode_rule
from ..models import Seqrun
from ..models import Seqrun_attribute
from ..models import Seqrun_stats
from ..models import Collection
from ..models import Collection_attribute
from ..models import Collection_group
from ..models import File
from ..models import File_attribute
from ..models import Pipeline
from ..models import Pipeline_seed
from ..models import Analysis
from .. import db

def cleanup_and_load_new_data_to_metadata_tables(input_json, cleanup=True):
    try:
        if not os.path.exists(input_json):
            raise IOError("Input file {0} not found".format(input_json))
        with open(input_json, "rb") as fp:
            json_data = json.load(fp)
        if not isinstance(json_data, dict):
            raise TypeError('No dictionary found for metadata update')
        delete_order_tables = [
            File_attribute,
            File,
            Collection_attribute,
            Collection,
            Collection_group,
            Pipeline_seed,
            Pipeline,
            Analysis,
            Platform,
            Flowcell_barcode_rule,
            Seqrun_attribute,
            Seqrun_stats,
            Seqrun,
            Run_attribute,
            Run,
            Experiment_attribute,
            Experiment,
            Sample_attribute,
            Sample,
            Project_attribute,
            Project,
            IgfUser,
            ProjectUser]
        create_order_tables = [
            Project,
            Analysis,
            IgfUser,
            ProjectUser,
            Sample,
            Sample_attribute,
            Experiment,
            Experiment_attribute,
            Platform,
            Flowcell_barcode_rule,
            Seqrun,
            Seqrun_stats,
            Seqrun_attribute,
            Run,
            Run_attribute,
            Pipeline,
            Pipeline_seed,
            Collection,
            Collection_attribute,
            File,
            Collection_group,
            File_attribute]
        try:
            for table in delete_order_tables:
                if table.__tablename__ in json_data.keys():
                    db.session.query(table).delete()
            for table in create_order_tables:
                if table.__tablename__ in json_data.keys():
                    table_data = json_data.get(table.__tablename__)
                    df = pd.DataFrame(table_data)
                    if table.__tablename__=='project_user':
                        pass
                    elif table.__tablename__=='sample':
                        df['taxon_id'] = df['taxon_id'].fillna(0)
                        df.fillna('', inplace=True)
                    else:
                        df.fillna('', inplace=True)
                    db.session.\
                        bulk_insert_mappings(
                            table,
                            df.to_dict(orient="records"))
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError("Failed to load data db, error: {0}".format(e))
        finally:
            if cleanup:
                os.remove(input_json)
    except Exception as e:
        raise ValueError("Failed to load new metadata, error: {0}".format(e))


def check_for_projects_in_metadata_db(project_list):
    try:
        errors = list()
        results = \
            db.session.\
                query(Project.project_igf_id).\
                filter(Project.project_igf_id.in_(project_list)).\
                all()
        results = [
            i[0] if isinstance(i, tuple) else i
                for i in results]
        output = dict()
        for i in project_list:
            if i in results:
                output.update({i: True})
            else:
                output.update({i: False})
        for key, val in output.items():
            if not val:
                errors.\
                    append(
                        "Project {0} is missing in db".\
                            format(key))
        return output, errors
    except Exception as e:
        raise ValueError(
                "Failed to check projects in db, error: {0}".\
                    format(e))


def check_sample_and_project_ids_in_metadata_db(
    sample_project_list: list,
    check_user: bool = True,
    check_missing: bool =True) -> list:
    try:
        input_sample_project_dict = dict()
        input_username_list = list()
        output_sample_project_dict = dict()
        errors = list()
        for entry in sample_project_list:
            if 'sample_igf_id' not in entry.keys() or \
               'project_igf_id' not in entry.keys():
               raise KeyError(
                        "Missing sample id or project id in {0}".\
                            format(entry))
            if entry.get('sample_igf_id') is not None and \
               entry.get('project_igf_id') is not None:
                input_sample_project_dict.\
                    update({entry.get('sample_igf_id'): entry.get('project_igf_id')})
            else:
                errors.append('Missing data found in entry: {0}'.format(entry))
            if check_user:
                if 'name' not in entry.keys() or \
                   'email_id' not in entry.keys():
                    raise KeyError('Missing name or email id from metadata: {0}'.format(entry))
                if entry.get('name') is not None and \
                   entry.get('email_id') is not None:
                    input_username_list.\
                        append({'name': entry.get('name'), 'email_id': entry.get('email_id')})
                else:
                    errors.append('Missing data found in entry: {0}'.format(entry))
        if check_user:
            # check for name and email mismatch
            name_email_errors = \
                check_user_name_and_email_in_metadata_db(
                    name_email_list=input_username_list,
                    check_missing=False)
            if len(name_email_errors) > 0:
                errors.extend(name_email_errors)
        results = \
            db.session.\
                query(Sample.sample_igf_id, Project.project_igf_id).\
                join(Project, Project.project_id==Sample.project_id).\
                filter(Sample.sample_igf_id.in_(input_sample_project_dict.keys())).\
                all()
        for entry in results:
            output_sample_project_dict.\
                update({entry[0]: entry[1]})
        for sample, project in input_sample_project_dict.items():
            if sample not in output_sample_project_dict and \
               check_missing:
                errors.\
                    append(
                        'Missing metadata for sample {0}'.\
                            format(sample))
            if sample in output_sample_project_dict and \
               project != output_sample_project_dict.get(sample):
               errors.\
                   append(
                       "Sample {0} is linked to project {1}, not {2}".\
                           format(
                               sample,
                               output_sample_project_dict.get(sample),
                               project))
        return errors
    except Exception as e:
        raise ValueError(
                "Failed to check sample projects in db, error: {0}".\
                    format(e))

def get_email_ids_for_user_name(name_list: list) -> dict:
    try:
        results = \
            db.session.\
                query(IgfUser.name, IgfUser.email_id).\
                filter(IgfUser.name.in_(name_list)).\
                all()
        results = {
            i[0]: i[1]
                for i in results}
        return results
    except Exception as e:
        raise ValueError("Failed fetch email ids for user name, error: {0}".format(e))


def get_names_for_user_email(email_list: list) -> dict:
    try:
        results = \
            db.session.\
                query(IgfUser.email_id, IgfUser.name).\
                filter(IgfUser.email_id.in_(email_list)).\
                all()
        results = {
            i[0]: i[1]
                for i in results}
        return results
    except Exception as e:
        raise ValueError()


def check_user_name_and_email_in_metadata_db(
    name_email_list: list,
    name_column: str = 'name',
    email_column: str = 'email_id',
    check_missing: bool = True) -> list:
    try:
        for entry in name_email_list:
            if entry.get(name_column) is None or \
               entry.get(email_column) is None:
               raise KeyError("Missing name or email id in the input list")
            df = pd.DataFrame(name_email_list)
            name_list = \
                df[name_column].\
                    drop_duplicates().\
                    values.\
                    tolist()
            email_list = \
                df[email_column].\
                    drop_duplicates().\
                    values.\
                    tolist()
            name_dict = \
                get_email_ids_for_user_name(
                    name_list)
            email_dict = \
                get_names_for_user_email(
                    email_list)
            errors = list()
            for entry in name_email_list:
                name = entry.get('name')
                email_id = entry.get('email_id')
                if name_dict.get(name) is None and check_missing:
                    errors.append('Missing name {0} in db'.format(name))
                if email_dict.get(email_id) is None and check_missing:
                    errors.append('Missing email {0} in db'.format(email_id))
                if name_dict.get(name) is not None and \
                   email_id != name_dict.get(name):
                   errors.append(
                       "User {0} registered with email id {1}, not {2}".\
                           format(name, name_dict.get(name), email_id))
                if email_dict.get(email_id) is not None and \
                   name != email_dict.get(email_id):
                   errors.append(
                       "Email {0} registered with name {1}, not {2}".\
                           format(email_id, email_dict.get(email_id), name))
        return errors
    except Exception as e:
        raise ValueError(
                "Failed to compate user name and email in db, error: {0}".\
                    format(e))