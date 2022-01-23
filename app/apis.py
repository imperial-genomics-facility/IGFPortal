import json, logging
from flask_appbuilder import ModelRestApi
from flask import request
from flask_appbuilder.api import BaseApi, expose, rison, safe
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import appbuilder, db
from .models import IlluminaInteropData

"""
InterOp data
"""
def search_interop_for_run(run_name):
    try:
        result = \
            db.session.\
            query(IlluminaInteropData).\
            filter(IlluminaInteropData.run_name==run_name).one_or_none()
        return result
    except Exception as e:
        raise ValueError("Failed lookup for interop data, error: {0}".format(e))


def add_interop_data(run_data):
    try:
        if isinstance(run_data, str):
            run_data = json.loads(run_data)
        if isinstance(run_data, bytes):
            run_data = json.loads(run_data.decode())
        interop_entry = \
            IlluminaInteropData(
                run_name = run_data.get('run_name'),
                table_data = run_data.get('table_data'),
                flowcell_data = run_data.get('flowcell_data'),
                intensity_data = run_data.get('intensity_data'),
                cluster_count_data = run_data.get('cluster_count_data'),
                density_data = run_data.get('density_data'),
                qscore_bins_data = run_data.get('qscore_bins_data'),
                qsocre_cycles_data = run_data.get('qsocre_cycles_data'),
                occupied_pass_filter = run_data.get('occupied_pass_filter'))
        try:
            db.session.add(interop_entry)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
        raise ValueError("Failed adding interop data, error: {0}".format(e))

def edit_interop_data(run_data):
    try:
        if isinstance(run_data, str):
            run_data = json.loads(run_data)
        if isinstance(run_data, bytes):
            run_data = json.loads(run_data.decode())
        if "run_name" not in run_data:
            raise ValueError("Missing run name")
        try:
            db.session.\
                query(IlluminaInteropData).\
                filter(IlluminaInteropData.run_name==run_data.get("run_name")).\
                update(run_data)
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
        raise ValueError("Failed to update interop data, error: {0}".format(e))


def add_or_edit_interop_data(run_data):
    try:
        if isinstance(run_data, str):
            run_data = json.loads(run_data)
        if isinstance(run_data, bytes):
            run_data = json.loads(run_data.decode())
        if "run_name" not in run_data:
            raise ValueError("Missing run name")
        result = \
            search_interop_for_run(
                run_name=run_data.get('run_name'))
        if result is None:
            add_interop_data(run_data=run_data)
        else:
            edit_interop_data(run_data=run_data)
    except Exception as e:
        raise ValueError("Failed to add or edit interop data, error: {0}".format(e))


class SeqrunInteropApi(ModelRestApi):
    resource_name = "interop_data"
    datamodel = SQLAInterface(IlluminaInteropData)

    @expose('/search_run')
    @rison()
    def search_run(self, **kwargs):
        try:
            if "run_name" in kwargs['rison']:
                message = 'EXIST'
                result = \
                    search_interop_for_run(
                        run_name=kwargs['rison']['run_name'])
                if result is None:
                    message = 'NOT EXIST'
                return self.response(200, message=message)
            return self.response_400(message="Please send run_name")
        except Exception as e:
            logging.error(e)

    @expose('/add_run', methods=['POST'])
    @protect()
    def add_run(self):
        try:
            if not request.files:
                return self.response_400('No files')
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            file_obj.seek(0)
            run_data = file_obj.read()
            add_interop_data(run_data=run_data)
            return self.response(200, message='added run data')
        except Exception as e:
            logging.error(e)

    @expose('/edit_run',  methods=['POST'])
    @protect()
    def edit_run(self):
        try:
            if not request.files:
                return self.response_400('No files')
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            file_obj.seek(0)
            run_data = file_obj.read()
            edit_interop_data(run_data=run_data)
            return self.response(200, message='updated run data')
        except Exception as e:
            logging.error(e)

    @expose('/add_or_edit_run',  methods=['POST'])
    @protect()
    def add_or_edit_run(self):
        try:
            if not request.files:
                return self.response_400('No files')
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            file_obj.seek(0)
            run_data = file_obj.read()
            add_or_edit_interop_data(run_data)
            return self.response(200, message='successfully added or updated run data')
        except Exception as e:
            logging.error(e)

appbuilder.add_api(SeqrunInteropApi)