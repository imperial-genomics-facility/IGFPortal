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