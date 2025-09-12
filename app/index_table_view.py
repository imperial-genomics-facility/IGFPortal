import logging
import pandas as pd
from flask import g
from typing import Tuple
from datetime import datetime
from io import BytesIO, StringIO
from flask_appbuilder.security.decorators import has_access
from wtforms_sqlalchemy.fields import QuerySelectField
from wtforms.fields import SelectField
from flask_appbuilder.fieldwidgets import Select2Widget
from flask_appbuilder import ModelView
from .models import SampleIndex, ProjectIndex
from flask import redirect, flash, send_file
from flask_appbuilder.actions import action
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.baseviews import expose
from . import db


log = logging.getLogger(__name__)

class ProjectIndexView(ModelView):
    datamodel = SQLAInterface(ProjectIndex)
    base_permissions = ['can_list', 'can_show', 'can_add', 'can_edit', 'can_get_index_for_project']
    list_columns = ['project_tag', 'sample_table', 'update_time']
    show_columns = ['project_tag', 'project_csv_data']
    add_columns = ['project_tag', 'project_csv_data']
    edit_columns = ['project_csv_data']
    label_columns = {
        "project_tag": "Project Tag",
        "project_csv_data": "CSV Data",
        "update_time": "Updated on"}

    @expose('/project_sample_index/<int:id>')
    @has_access
    def get_index_for_project(self, id):
        try:
            columns, project_name, sample_records = \
                get_sample_index_for_project(
                    project_index_id=id)
            return \
            self.render_template(
                "sample_index_view.html",
                project_name=project_name,
                columns=columns,
                table_data=sample_records
            )
        except Exception as e:
            log.error(e)
            flash(e, 'danger')
            return redirect('/project_index')


    @action("download_sample_index_csv", "Download csv", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
    def download_sample_index_csv(self, item):
        try:
            output = BytesIO()
            columns, project_name, sample_records = \
                get_sample_index_for_project(
                    project_index_id=item.project_index_id,
                    get_original_col_names=True)
            file_name = f'{project_name}.csv'
            if len(sample_records) > 0:
                df = \
                    pd.DataFrame(sample_records, columns=columns)
            else:
                df = pd.DataFrame(columns=columns)
            df.fillna('', inplace=True)
            df.to_csv(output, index=False)
            output.seek(0)
            self.update_redirect()
            return send_file(output, download_name=file_name, as_attachment=True)
        except Exception as e:
            log.error(e)
            flash('Failed to create csv', 'danger')


    @action("load_sample_index_csv", "Load csv data", confirmation="Upload to portal ?", icon="fa-rocket", multiple=True, single=False)
    def load_sample_index_csv(self, items):
        try:
            for item in items:
                cvsStringIO = StringIO(item.project_csv_data.strip())
                df = pd.read_csv(cvsStringIO, header=0)
                df.fillna('', inplace=True)
                sample_list = \
                    df.to_dict(orient='records')
                try:
                    ## load csv data to sample_index table
                    create_or_update_sample_index_data(
                        sample_list=sample_list,
                        project_index_id=item.project_index_id,
                        user_id=g.user.id)
                    ## reset project_csv_data to empty
                    db.session.\
                        query(ProjectIndex).\
                        filter(ProjectIndex.project_index_id == item.project_index_id).\
                        update({'project_csv_data': ''})
                    db.session.commit()
                    flash(f'Loaded indices for {item.project_tag}', 'success')
                except Exception as e:
                    flash(f'Failed to load csv for {item.project_tag}', 'danger')
                    log.error(e)
                    raise
            self.update_redirect()
            return redirect(self.get_redirect())
        except Exception as e:
            log.error(e)
            raise


def create_or_update_sample_index_data(
        sample_list: list,
        project_index_id: int,
        user_id: int) \
            -> bool:
    try:
        for sample_entry in sample_list:
            # check sample index exists
            ## look for existing sample record
            if 'sample_name' not in sample_entry or \
               'i7_index_name' not in sample_entry or \
               'i7_index' not in sample_entry:
                raise Exception('Missing sample index data')
            sample_name = \
                sample_entry.get('sample_name')
            sample_in_db = \
                db.session.\
                    query(SampleIndex.sample_index_id).\
                    filter(SampleIndex.sample_name == sample_name).\
                    filter(SampleIndex.project_index_id == project_index_id).\
                    one_or_none()
            if sample_in_db is None:
                ## create new entry
                ## add project index id
                if 'project_index_id' not in sample_entry:
                    sample_entry['project_index_id'] = project_index_id
                ## add user id for audit cols
                if 'created_by_fk' not in sample_entry:
                    sample_entry['created_by_fk'] = user_id
                ## add datestamp
                if 'created_on' not in sample_entry:
                    sample_entry['created_on'] = datetime.now()
                sample_index = \
                    SampleIndex(**sample_entry)
                db.session.add(sample_index)
                db.session.flush()
            else:
                ## update existing entry
                ## add user id for audit cols
                if 'changed_by_fk' not in sample_entry:
                    sample_entry['changed_by_fk'] = user_id
                if 'changed_on' not in sample_entry:
                    sample_entry['changed_on'] = datetime.now()
                db.session.\
                    query(SampleIndex).\
                    filter(SampleIndex.sample_name == sample_name).\
                    filter(SampleIndex.project_index_id == project_index_id).\
                    update(sample_entry)
                db.session.flush()
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        log.error(e)
        raise

def get_sample_index_for_project(
      project_index_id: int,
      get_original_col_names: bool = False) \
        -> Tuple[list, str, list]:
    try:
        columns = [
            "Sample name",
            "IGF ID",
            "Container ID",
            "RIN score",
            "Well position",
            "Pool ID",
            "I7 index name",
            "I7 index",
            "I5 index name",
            "I5 index",
            "Avg region molarity",
            "Avg fragment size"
        ]
        original_columns = [
            "sample_name",
            "igf_id",
            "container_id",
            "rin_score",
            "well_position",
            "pool_id",
            "i7_index_name",
            "i7_index",
            "i5_index_name",
            "i5_index",
            "avg_region_molarity",
            "avg_fragment_size"
        ]
        project_name = \
            db.session.\
                query(ProjectIndex.project_tag).\
                filter(ProjectIndex.project_index_id == project_index_id).\
                one_or_none()
        if project_name is not None and \
           isinstance(project_name, tuple):
            project_name = project_name[0]
        results = \
            db.session.\
                query(
                    SampleIndex.sample_name,
                    SampleIndex.igf_id,
                    SampleIndex.container_id,
                    SampleIndex.rin_score,
                    SampleIndex.well_position,
                    SampleIndex.pool_id,
                    SampleIndex.i7_index_name,
                    SampleIndex.i7_index,
                    SampleIndex.i5_index_name,
                    SampleIndex.i5_index,
                    SampleIndex.avg_region_molarity,
                    SampleIndex.avg_fragment_size
                    ).\
                filter(SampleIndex.project_index_id == project_index_id).\
                order_by(SampleIndex.sample_index_id.desc()).\
                all()
        if get_original_col_names:
            return original_columns, project_name, results
        else:
            return columns, project_name, results
    except Exception as e:
        log.error(e)
        raise


def project_index_query():
    results = \
        db.session.\
            query(ProjectIndex).\
            order_by(ProjectIndex.project_index_id.desc()).\
            limit(100).\
            all()
    return results


class SampleIndexView(ModelView):
    datamodel = SQLAInterface(SampleIndex)
    list_columns = [
        "project_index.project_tag",
        "sample_name",
        "igf_id",
        "container_id",
        "well_position",
        "pool_id"
        ]
    base_permissions = ['can_list', 'can_show', 'can_edit']
    show_columns = [
        "project_index.project_tag",
        "sample_name",
        "igf_id",
        "container_id",
        "rin_score",
        "well_position",
        "pool_id",
        "i7_index_name",
        "i7_index",
        "i5_index_name",
        "i5_index",
        "avg_region_molarity",
        "avg_fragment_size"
        ]
    edit_columns = [
        "project_index",
        "sample_name",
        "igf_id",
        "container_id",
        "rin_score",
        "well_position",
        "pool_id",
        "i7_index_name",
        "i7_index",
        "i5_index_name",
        "i5_index",
        "avg_region_molarity",
        "avg_fragment_size"
        ]
    add_form_extra_fields = {
        "project_index": QuerySelectField(
            "ProjectIndex",
            query_factory=project_index_query,
            widget=Select2Widget()
        ),
        "well_position": SelectField("Well Position", choices=[f'{w}{i}' for w in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] for i in range(1, 13)]),
    }
    edit_form_extra_fields = {
        "project_index": QuerySelectField(
            "ProjectIndex",
            query_factory=project_index_query,
            widget=Select2Widget()
        ),
        "well_position": SelectField("Well Position", choices=[f'{w}{i}' for w in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H'] for i in range(1, 13)])
    }