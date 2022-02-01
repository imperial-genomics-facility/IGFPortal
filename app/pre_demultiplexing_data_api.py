import json, logging
from flask_appbuilder import ModelRestApi
from flask import request
from flask_appbuilder.api import expose
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder.security.decorators import protect
from . import db
from .models import PreDeMultiplexingData

"""
    Pre-demultiplexing data Api
"""
def search_predemultiplexing_data(run_name, samplesheet_tag):
    try:
        result = \
            db.session.\
            query(PreDeMultiplexingData).\
            filter(PreDeMultiplexingData.run_name==run_name).\
            filter(PreDeMultiplexingData.samplesheet_tag==samplesheet_tag).\
            one_or_none()
        return result
    except Exception as e:
        raise ValueError(
                "Failed to search pre demultiplexing data, error: {0}".\
                    format(e))


def add_predemultiplexing_data(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, bytes):
            data = json.loads(data.decode())
        predemult_data = \
            PreDeMultiplexingData(
                run_name=data.get("run_name"),
                samplesheet_tag=data.get("samplesheet_tag"),
                flowcell_cluster_plot=data.get("flowcell_cluster_plot"),
                project_summary_table=data.get("project_summary_table"),
                project_summary_plot=data.get("project_summary_plot"),
                sample_table=data.get("sample_table"),
                sample_plot=data.get("sample_plot"),
                undetermined_table=data.get("undetermined_table"),
                undetermined_plot=data.get("undetermined_plot"))
        try:
            db.session.add(predemult_data)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
        raise ValueError(
                "Failed to add de-multiplex data, error: {0}".\
                    format(e))

def edit_predemultiplexing_data(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, bytes):
            data = json.loads(data.decode())
        if "run_name" not in data:
            raise ValueError("Missing run name")
        if "samplesheet_tag" not in data:
            raise ValueError("Missing sampleshheet tag")
        try:
            db.session.\
                query(PreDeMultiplexingData).\
                filter(PreDeMultiplexingData.run_name==data.get("run_name")).\
                filter(PreDeMultiplexingData.samplesheet_tag==data.get("samplesheet_tag")).\
                update(data)
            db.session.commit()
        except:
            db.session.rollback()
            raise
    except Exception as e:
        raise ValueError(
                "Failed to update de-multiplex data, error: {0}".\
                    format(e))


def add_or_edit_predemultiplexing_data(data):
    try:
        if isinstance(data, str):
            data = json.loads(data)
        if isinstance(data, bytes):
            data = json.loads(data.decode())
        if "run_name" not in data:
            raise ValueError("Missing run name")
        if "samplesheet_tag" not in data:
            raise ValueError("Missing sampleshheet tag")
        result = \
            search_predemultiplexing_data(
                run_name=data.get("run_name"),
                samplesheet_tag=data.get("samplesheet_tag"))
        if result is None:
            add_predemultiplexing_data(data=data)
        else:
            edit_predemultiplexing_data(data=data)
    except Exception as e:
        raise ValueError(
                "Failed to add or update de-multiplex data, error: {0}".\
                    format(e))


class PreDeMultiplexingDataApi(ModelRestApi):
    resource_name = "predemultiplexing_data"
    datamodel = SQLAInterface(PreDeMultiplexingData)

    @expose('/add_or_edit_report',  methods=['POST'])
    @protect()
    def add_or_edit_demult_report(self):
        try:
            if not request.files:
                return self.response_400('No files')
            file_objs = request.files.getlist('file')
            file_obj = file_objs[0]
            file_obj.seek(0)
            json_data = file_obj.read()
            add_or_edit_predemultiplexing_data(data=json_data)
            return self.response(200, message='successfully added or updated demult data')
        except Exception as e:
            logging.error(e)


