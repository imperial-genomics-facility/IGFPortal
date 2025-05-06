import os
import json
import typing
import tempfile
from typing import Tuple
import pandas as pd
from dateutil.parser import parse
from ..models import (
    Project,
    IgfUser,
    ProjectUser,
    Project_attribute,
    Sample,
    Sample_attribute,
    Experiment,
    Experiment_attribute,
    Run,
    Run_attribute,
    Platform,
    Flowcell_barcode_rule,
    Seqrun,
    Seqrun_attribute,
    Seqrun_stats,
    Collection,
    Collection_attribute,
    Collection_group,
    File,
    File_attribute,
    Pipeline,
    Pipeline_seed,
    Analysis,
    RawAnalysis,
    RawAnalysisValidationSchema,
    RawAnalysisTemplate,
    Project_info_data,
    Project_seqrun_info_data,
    Project_seqrun_info_file,
    Project_analysis_info_data,
    Project_analysis_info_file,
    RDSProject_backup)
from .. import db

def backup_specific_portal_tables(json_file: str) -> str:
    try:
        backup_order = [
            RawAnalysis,
            RawAnalysisValidationSchema,
            RawAnalysisTemplate,
            Project_info_data,
            Project_seqrun_info_data,
            Project_seqrun_info_file,
            Project_analysis_info_data,
            Project_analysis_info_file,
            RDSProject_backup
        ]
        db_data = dict()
        for table_name in backup_order:
            data = \
                pd.read_sql(
                    table_name.__tablename__,
                    db.session.bind)
            if table_name.__tablename__=='raw_analysis':
                data['date_stamp'] = \
                    data['date_stamp'].astype(str)
            if table_name.__tablename__=='raw_analysis_validation_schema':
                data['date_stamp'] = \
                    data['date_stamp'].astype(str)
            if table_name.__tablename__=='project_seqrun_info_file':
                data['date_created'] = \
                    data['date_created'].astype(str)
            if table_name.__tablename__=='project_seqrun_info_file':
                data['date_updated'] = \
                    data['date_updated'].astype(str)
            if table_name.__tablename__=='project_analysis_info_file':
                data['date_created'] = \
                    data['date_created'].astype(str)
            if table_name.__tablename__=='project_analysis_info_file':
                data['date_updated'] = \
                    data['date_updated'].astype(str)
            if table_name.__tablename__=='rds_project_backup':
                data['date_stamp'] = \
                    data['date_stamp'].astype(str)
            # if table_name.__tablename__=='raw_analysis':
            #     data = \
            #         pd.read_sql(
            #             table_name.__tablename__,
            #             db.session.bind,
            #             parse_dates=["date_stamp"])
            # if table_name.__tablename__=='raw_analysis_validation_schema':
            #     data = \
            #         pd.read_sql(
            #             table_name.__tablename__,
            #             db.session.bind,
            #             parse_dates=["date_stamp"])
            # if table_name.__tablename__=='project_seqrun_info_file':
            #     data = \
            #         pd.read_sql(
            #             table_name.__tablename__,
            #             db.session.bind,
            #             parse_dates=["date_created", "date_updated"])
            # if table_name.__tablename__=='project_analysis_info_file':
            #     data = \
            #         pd.read_sql(
            #             table_name.__tablename__,
            #             db.session.bind,
            #             parse_dates=["date_created", "date_updated"])
            # if table_name.__tablename__=='rds_project_backup':
            #     data = \
            #         pd.read_sql(
            #             table_name.__tablename__,
            #             db.session.bind,
            #             parse_dates=["date_stamp"])
            db_data.update({
                table_name.__tablename__: data.to_dict(orient="records")})
        with open(json_file, 'w') as fp:
            json.dump(db_data, fp)
        return json_file
    except Exception as e:
        raise ValueError(
            f"Failed to backup portal tables, error: {e}")


def cleanup_and_load_new_data_to_metadata_tables(
    input_json: str,
    cleanup: bool=True) -> None:
    try:
        if not os.path.exists(input_json):
            raise IOError("Input file {0} not found".format(input_json))
        with open(input_json, "rb") as fp:
            json_data = json.load(fp)
        if not isinstance(json_data, dict):
            raise TypeError('No dictionary found for metadata update')
        ## get a tmp json file
        (_, json_file) = \
            tempfile.mkstemp(
                suffix='.json',
                prefix='portal_metadata_',)
        ## backup portal data
        json_file = \
            backup_specific_portal_tables(json_file)
        # with open(json_file, 'r') as fp:
        #     t_data = fp.read()
        # print(t_data)
        ## backup main db
        delete_order_tables = [
            Pipeline_seed,
            Pipeline,
            Analysis,
            Platform,
            Flowcell_barcode_rule,
            Seqrun,
            Run_attribute,
            Run,
            Experiment,
            Sample,
            Project,
            IgfUser,
            ProjectUser]
        create_order_tables = [
            Project,
            Analysis,
            IgfUser,
            ProjectUser,
            Sample,
            Experiment,
            Platform,
            Flowcell_barcode_rule,
            Seqrun,
            Run,
            Run_attribute,
            Pipeline,
            Pipeline_seed]
        portal_backup_order = [
            RawAnalysis,
            RawAnalysisValidationSchema,
            RawAnalysisTemplate,
            Project_info_data,
            Project_seqrun_info_data,
            Project_seqrun_info_file,
            Project_analysis_info_data,
            Project_analysis_info_file,
            RDSProject_backup
        ]
        portal_delete_order = [
            RawAnalysisValidationSchema,
            RawAnalysisTemplate,
            RawAnalysis,
            Project_seqrun_info_data,
            Project_seqrun_info_file,
            Project_analysis_info_data,
            Project_analysis_info_file,
            Project_info_data,
            RDSProject_backup
        ]
        try:
            ## delete main tables
            for table in delete_order_tables:
                if table.__tablename__ in json_data.keys():
                    db.session.query(table).delete()
            ## delete portal tables
            with open(json_file, 'r') as fp:
                # t_data = fp.read()
                portal_json_data = json.load(fp)
            #print(portal_json_data)
            for table in portal_delete_order:
                if table.__tablename__ in portal_json_data.keys():
                    db.session.query(table).delete()
            ## load main data
            for table in create_order_tables:
                if table.__tablename__ in json_data.keys():
                    table_data = json_data.get(table.__tablename__)
                    df = pd.DataFrame(table_data)
                    ## project
                    if table.__tablename__=='project' and \
                       'start_timestamp' in df.columns:
                        df['start_timestamp'] = \
                            pd.to_datetime(df.start_timestamp)
                    ## user
                    if table.__tablename__=='user' and \
                       'start_timestamp' in df.columns:
                        df['date_created'] = \
                            pd.to_datetime(df.date_created)
                    ## sample
                    if table.__tablename__=='sample':
                        if 'date_created' in df.columns:
                            df['date_created'] = \
                                pd.to_datetime(df.date_created)
                        if 'taxon_id' in df.columns:
                            df['taxon_id'] = \
                                df['taxon_id'].fillna(0)
                        df.fillna('', inplace=True)
                    ## platform
                    if table.__tablename__=='platform' and \
                       'date_created' in df.columns:
                        df['date_created'] = \
                            pd.to_datetime(df.date_created)
                    ## seqrun
                    if table.__tablename__=='seqrun' and \
                       'date_created' in df.columns:
                        df['date_created'] = \
                            pd.to_datetime(df.date_created)
                    ## experiment
                    if table.__tablename__=='experiment' and \
                       'date_created' in df.columns:
                        df['date_created'] = \
                            pd.to_datetime(df.date_created)
                    ## run
                    if table.__tablename__=='run' and \
                       'date_created' in df.columns:
                        df['date_created'] = \
                            pd.to_datetime(df.date_created)
                    # ## collection
                    # if table.__tablename__=='collection' and \
                    #    'date_stamp' in df.columns:
                    #     df['date_stamp'] = \
                    #         pd.to_datetime(df.date_stamp)
                    # ## file
                    # if table.__tablename__=='file' and \
                    #    'date_created' in df.columns and \
                    #    'date_updated' in df.columns:
                    #     df['date_created'] = \
                    #         pd.to_datetime(df.date_created)
                    #     df['date_updated'] = \
                    #         pd.to_datetime(df.date_updated)
                    ## pipeline
                    if table.__tablename__=='pipeline' and \
                       'date_stamp' in df.columns:
                        df['date_stamp'] = \
                            pd.to_datetime(df.date_stamp)
                    ## pipeline_seed
                    if table.__tablename__=='pipeline_seed' and \
                       'date_stamp' in df.columns:
                        df['date_stamp'] = \
                            pd.to_datetime(df.date_stamp)
                    ## fill NA
                    if table.__tablename__=='project_user':
                        pass
                    else:
                        df.fillna('', inplace=True)
                    db.session.\
                        bulk_insert_mappings(
                            table,
                            df.to_dict(orient="records"))
            ## load portal data
            for table in portal_backup_order:
                if table.__tablename__ in portal_json_data.keys():
                    table_data = portal_json_data.get(table.__tablename__)
                    df = pd.DataFrame(table_data)
                    ## raw_analysis
                    if table.__tablename__ == 'raw_analysis' and \
                       'date_stamp' in df.columns:
                        df['date_stamp'] = \
                            pd.to_datetime(df.date_stamp)
                    ## raw_analysis_validation_schema
                    if table.__tablename__ == 'raw_analysis_validation_schema' and \
                       'date_stamp' in df.columns:
                        df['date_stamp'] = \
                            pd.to_datetime(df.date_stamp)
                    ## project_seqrun_info_file
                    if table.__tablename__ == 'project_seqrun_info_file' and \
                       'date_created' in df.columns and \
                       'date_updated' in df.columns:
                        df['date_created'] = \
                            pd.to_datetime(df.date_created)
                        df['date_updated'] = \
                            pd.to_datetime(df.date_updated)
                    ## project_analysis_info_file
                    if table.__tablename__ == 'project_analysis_info_file' and \
                       'date_created' in df.columns and \
                       'date_updated' in df.columns:
                        df['date_created'] = \
                            pd.to_datetime(df.date_created)
                        df['date_updated'] = \
                            pd.to_datetime(df.date_updated)
                    ## rds_project_backup
                    if table.__tablename__ == 'rds_project_backup' and \
                       'date_stamp' in df.columns:
                        df['date_stamp'] = \
                            pd.to_datetime(df.date_stamp)
                    ## project_index
                    if table.__tablename__ == 'project_index' and \
                       'update_time' in df.columns:
                        df['update_time'] = \
                            pd.to_datetime(df.update_time)
                    ## load data
                    db.session.\
                        bulk_insert_mappings(
                            table,
                            df.to_dict(orient="records"))
            ## save all changes
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(
                f"Failed to load data db, error: {e}")
        ## load collection tables
        try:
            delete_order_tables = [
                Collection_group,
                File,
                Collection
            ]
            create_order_tables = [
                Collection,
                File,
                Collection_group
            ]
            for table in delete_order_tables:
                if table.__tablename__ in json_data.keys():
                    db.session.query(table).delete()
             ## load main data
            for table in create_order_tables:
                if table.__tablename__ in json_data.keys():
                    table_data = json_data.get(table.__tablename__)
                    df = pd.DataFrame(table_data)
                    ## collection
                    if table.__tablename__=='collection' and \
                       'date_stamp' in df.columns:
                        df['date_stamp'] = \
                            pd.to_datetime(df.date_stamp)
                    ## file
                    if table.__tablename__=='file' and \
                       'date_created' in df.columns and \
                       'date_updated' in df.columns:
                        df['date_created'] = \
                            pd.to_datetime(df.date_created)
                        df['date_updated'] = \
                            pd.to_datetime(df.date_updated)
                    df.fillna('', inplace=True)
                    db.session.\
                        bulk_insert_mappings(
                            table,
                            df.to_dict(orient="records"))
            ## save all changes
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            raise ValueError(
                f"Failed to load collection data to db, error: {e}")
        finally:
            if cleanup:
                os.remove(input_json)
    except Exception as e:
        raise ValueError("Failed to load new metadata, error: {0}".format(e))


def check_for_projects_in_metadata_db(
    project_list: list,
    flag_existing_project: bool = False) -> \
        Tuple[dict, list]:
    """
    Check if project ids are present in metadata db

    :param project_list: List of project ids
    :param flag_existing_project: True if existing project ids should be checked
    :return: A tuple containing a dictionary with project id as key and True/False as value
             and a list of errors
    """
    try:
        errors = list()
        results = \
            db.session.\
                query(Project.project_igf_id).\
                filter(Project.project_igf_id.in_(project_list)).\
                all()
        results = [i[0] for i in results]
        output = dict()
        for i in project_list:
            if i in results:
                output.update({i: True})
            else:
                output.update({i: False})
        print(project_list)
        print(output)
        if flag_existing_project:
            for key, val in output.items():
                if val:
                    errors.append(
                        f"Project {key} is already present in db")
        else:
            for key, val in output.items():
                if not val:
                    errors.append(
                        f"Project {key} is missing in db")
        # for key, val in output.items():
        #     if not val:
        #         errors.\
        #             append(
        #                 "Project {0} is missing in db".\
        #                     format(key))
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