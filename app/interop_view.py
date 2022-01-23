import json
import logging
from flask import abort
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, SimpleFormView
from flask_appbuilder.baseviews import  expose
from . import db
from .models import IlluminaInteropData
from .forms import SeqrunInteropForm

"""
    InterOp data view
"""

def fetch_interop_data_by_id(run_id):
    try:
        results = \
            db.session.query(IlluminaInteropData).\
            filter(IlluminaInteropData.run_id==run_id).one_or_none()
        if results is None:
            abort(404)
        run_name = results.run_name
        intensity_data = results.intensity_data
        table_data = results.table_data
        flowcell_data = results.flowcell_data
        cluster_count_data = results.cluster_count_data
        density_data = results.density_data
        qscore_bins_data = results.qscore_bins_data
        qsocre_cycles_data = results.qsocre_cycles_data
        occupied_pass_filter = results.occupied_pass_filter
        date_stamp = results.date_stamp
        if intensity_data is not None or \
           intensity_data != "":
           intensity_data = json.loads(intensity_data)
        return run_name, intensity_data, table_data, flowcell_data, \
               cluster_count_data, density_data, qscore_bins_data, \
               qsocre_cycles_data, occupied_pass_filter, date_stamp
    except Exception as e:
        logging.error(e)


class IlluminaInteropDataView(ModelView):
    datamodel = SQLAInterface(IlluminaInteropData)
    label_columns = {'seqrun':'Sequencing run', 'date_stamp': 'Updated on'}
    list_columns = ['seqrun', 'date_stamp']
    base_permissions = ['can_list']

    @expose('/interop/<int:id>')
    def get_seqrun(self, id):
        (run_name, intensity_data, table_data, flowcell_data,
         cluster_count_data, density_data, qscore_bins_data,
         qscore_cycles_data, occupied_pass_filter, date_stamp) = \
            fetch_interop_data_by_id(run_id=id)
        chart_data = intensity_data.get("chart_data")
        labels = intensity_data.get("labels")
        flowcell_data = json.loads(flowcell_data)
        surface1_data = flowcell_data.get("surface1")
        surface2_data = flowcell_data.get("surface2")
        cluster_count_data = json.loads(cluster_count_data)
        density_data = json.loads(density_data)
        qscore_bins_data = json.loads(qscore_bins_data)
        qscore_cycles_data = json.loads(qscore_cycles_data)
        if occupied_pass_filter != '':
            occupied_pass_filter = json.loads(occupied_pass_filter)
        return \
            self.render_template(
                'interop.html',
                run_name=run_name,
                date_stamp=date_stamp,
                labels=labels,
                surface1=surface1_data,
                surface2=surface2_data,
                table_data=table_data,
                cluster_count_data=cluster_count_data,
                density_data=density_data,
                qscore_bins_data = qscore_bins_data,
                qsocre_cycles_data=qscore_cycles_data,
                occupied_pass_filter=occupied_pass_filter,
                chart_data=chart_data)

"""
def fetch_interop_data(run_name):
    results = \
        db.session.query(IlluminaInteropData).\
        filter(IlluminaInteropData.run_name==run_name).one_or_none()
    if results is None:
        abort(404)
    intensity_data = results.intensity_data
    table_data = results.table_data
    flowcell_data = results.flowcell_data
    cluster_count_data = results.cluster_count_data
    density_data = results.density_data
    qscore_bins_data = results.qscore_bins_data
    qsocre_cycles_data = results.qsocre_cycles_data
    occupied_pass_filter = results.occupied_pass_filter
    date_stamp = results.date_stamp
    if intensity_data is not None or \
       intensity_data != "":
       intensity_data = json.loads(intensity_data)
    return intensity_data, table_data, flowcell_data, \
           cluster_count_data, density_data, qscore_bins_data, \
           qsocre_cycles_data, occupied_pass_filter, date_stamp

class SeqrunInteropFormView(SimpleFormView):
    form = SeqrunInteropForm
    form_title = "Get Interop data"
    def form_post(self, form):
        (intensity_data, table_data, flowcell_data,
         cluster_count_data, density_data, qscore_bins_data,
         qsocre_cycles_data, occupied_pass_filter, date_stamp) = \
            fetch_interop_data(
                run_name=form.run_name.data.run_name)
        chart_data = intensity_data.get("chart_data")
        labels = intensity_data.get("labels")
        flowcell_data = json.loads(flowcell_data)
        surface1_data = flowcell_data.get("surface1")
        surface2_data = flowcell_data.get("surface2")
        cluster_count_data = json.loads(cluster_count_data)
        density_data = json.loads(density_data)
        qscore_bins_data = json.loads(qscore_bins_data)
        qsocre_cycles_data = json.loads(qsocre_cycles_data)
        if occupied_pass_filter != '':
            occupied_pass_filter = json.loads(occupied_pass_filter)
        return \
            self.render_template(
                'interop.html',
                run_name=form.run_name.data.run_name,
                date_stamp=date_stamp,
                labels=labels,
                surface1=surface1_data,
                surface2=surface2_data,
                table_data=table_data,
                cluster_count_data=cluster_count_data,
                density_data=density_data,
                qscore_bins_data = qscore_bins_data,
                qsocre_cycles_data=qsocre_cycles_data,
                occupied_pass_filter=occupied_pass_filter,
                chart_data=chart_data)
"""