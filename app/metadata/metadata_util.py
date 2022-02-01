import os, json
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


def check_sample_and_project_ids_in_metadata_db(sample_project_list, check_missing=True):
    try:
        input_sample_project_dict = dict()
        output_sample_project_dict = dict()
        errors = list()
        for entry in sample_project_list:
            if 'sample_igf_id' not in entry.keys() or \
               'project_igf_id' not in entry.keys():
               raise KeyError(
                        "Missing sample id or project id in {0}".\
                            format(entry))
            input_sample_project_dict.\
                update({entry.get('sample_igf_id'): entry.get('project_igf_id')})
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