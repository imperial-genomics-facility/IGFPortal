import json
import logging
from flask_appbuilder import has_access
from flask import render_template, redirect, flash, url_for, send_file, abort
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi, SimpleFormView
from flask_appbuilder.baseviews import BaseView, expose
from . import appbuilder, db
from .models import IlluminaInteropData, PreDeMultiplexingData
from .forms import SeqrunInteropForm

"""
Home view
"""
class HomeView(BaseView):
    route_base = "/"
    @expose('/user_home')
    def general(self):
        #greeting = "Hello {0}".format(g.user.username)
        return self.render_template('user_index.html')

    @expose('/admin_home')
    def admin_home(self):
        #greeting = "Hello {0}".format(g.user.username)
        return self.render_template('admin_index.html')


appbuilder.add_view_no_menu(HomeView())

"""
InterOp data view
"""

def fetch_interop_data_by_id(run_id):
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

class IlluminaInteropDataView(ModelView):
    datamodel = SQLAInterface(IlluminaInteropData)
    label_columns = {'seqrun':'Sequencing run', 'date_stamp': 'Updated on'}
    list_columns = ['seqrun', 'date_stamp']
    base_permissions = ['can_list']

    @expose('/interop/<int:id>')
    def get_seqrun(self, id):
        (run_name, intensity_data, table_data, flowcell_data,
         cluster_count_data, density_data, qscore_bins_data,
         qsocre_cycles_data, occupied_pass_filter, date_stamp) = \
            fetch_interop_data_by_id(run_id=id)
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
                run_name=run_name,
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
Pre de-multiplexing view
"""

class PreDeMultiplexingDataView(ModelView):
    datamodel = SQLAInterface(PreDeMultiplexingData)
    label_columns = {'run_name':'Sequencing run', 'samplesheet_tag':'Tag','date_stamp': 'Updated on', 'report': 'De-multiplexing report'}
    list_columns = ['run_name', 'samplesheet_tag', 'date_stamp', 'report']
    base_permissions = ['can_list']

    @expose('/predemult_report/<int:id>')
    def get_report(self, id):
        try:
            (run_name, samplesheet_tag, flowcell_cluster_plot, project_summary_table, project_summary_plot,
             sample_table, sample_plot, undetermined_table, undetermined_plot, date_stamp) = \
                get_pre_demultiplexing_data(demult_id=id)
            flowcell_labels = flowcell_cluster_plot.get('labels')
            total_cluster_raw = flowcell_cluster_plot.get('total_cluster_raw')
            total_cluster_pf = flowcell_cluster_plot.get('total_cluster_pf')
            total_yield = flowcell_cluster_plot.get('total_yield')
            lanes = list(sample_table.keys())
            return \
            self.render_template(
                'demultiplexing_report.html',
                run_name=run_name,
                date_stamp=date_stamp,
                flowcell_labels=flowcell_labels,
                total_cluster_raw=total_cluster_raw,
                total_cluster_pf=total_cluster_pf,
                total_yield=total_yield,
                project_summary_table=project_summary_table,
                project_summary_plot=project_summary_plot,
                sample_table=sample_table,
                sample_plot=sample_plot,
                undetermined_table=undetermined_table,
                undetermined_plot=undetermined_plot,
                lanes=lanes)
        except:
            logging.error(e)

def get_pre_demultiplexing_data(demult_id):
    result = \
        db.session.\
            query(PreDeMultiplexingData).\
            filter(PreDeMultiplexingData.demult_id==demult_id).\
            one_or_none()
    run_name = ''
    samplesheet_tag = ''
    flowcell_cluster_plot = ''
    project_summary_table = ''
    project_summary_plot = ''
    sample_table = ''
    undetermined_table = ''
    undetermined_plot = ''
    if result is not None:
        run_name = result.run_name
        samplesheet_tag = result.samplesheet_tag
        flowcell_cluster_plot = result.flowcell_cluster_plot
        if isinstance(flowcell_cluster_plot, str):
            flowcell_cluster_plot = json.loads(flowcell_cluster_plot)
        project_summary_table = result.project_summary_table
        project_summary_plot = result.project_summary_plot
        if isinstance(project_summary_plot, str):
            project_summary_plot = json.loads(project_summary_plot)
        sample_table = result.sample_table
        if isinstance(sample_table, str):
            sample_table = json.loads(sample_table)
        sample_plot = result.sample_plot
        if isinstance(sample_plot, str):
            sample_plot = json.loads(sample_plot)
        undetermined_table = result.undetermined_table
        if isinstance(undetermined_table, str):
            undetermined_table = json.loads(undetermined_table)
        undetermined_plot = result.undetermined_plot
        if isinstance(undetermined_plot, str):
            undetermined_plot = json.loads(undetermined_plot)
        date_stamp = result.date_stamp
    return run_name, samplesheet_tag, flowcell_cluster_plot, project_summary_table, project_summary_plot,\
           sample_table, sample_plot, undetermined_table, undetermined_plot, date_stamp




class TestPreDeMultiplexingDataView(BaseView):
    route_base = "/"
    @expose('/demult_data')
    def demult_data(self):
        (run_name, samplesheet_tag, flowcell_cluster_plot, project_summary_table, project_summary_plot,
         sample_table, sample_plot, undetermined_table, undetermined_plot, date_stamp) = \
            get_pre_demultiplexing_data(demult_id=1)
        flowcell_labels = flowcell_cluster_plot.get('labels')
        total_cluster_raw = flowcell_cluster_plot.get('total_cluster_raw')
        total_cluster_pf = flowcell_cluster_plot.get('total_cluster_pf')
        total_yield = flowcell_cluster_plot.get('total_yield')
        lanes = list(sample_table.keys())
        #lane1_table = sample_table.get(lanes[0])
        #sample_plot = sample_plot.get(lanes[0])
        #lane1_un_table = undetermined_table.get(lanes[0])
        #undetermined_plot = undetermined_plot.get(lanes[0])
        return \
            self.render_template(
                'demultiplexing_report.html',
                run_name=run_name,
                date_stamp=date_stamp,
                flowcell_labels=flowcell_labels,
                total_cluster_raw=total_cluster_raw,
                total_cluster_pf=total_cluster_pf,
                total_yield=total_yield,
                project_summary_table=project_summary_table,
                project_summary_plot=project_summary_plot,
                sample_table=sample_table,
                sample_plot=sample_plot,
                undetermined_table=undetermined_table,
                undetermined_plot=undetermined_plot,
                lanes=lanes)

"""
    Application wide 404 error handler
"""


@appbuilder.app.errorhandler(404)
def page_not_found(e):
    return (
        render_template(
            "404.html", base_template=appbuilder.base_template, appbuilder=appbuilder
        ),
        404,
    )

#appbuilder.add_view(
#    SeqrunInteropFormView,
#    "Search sequencing run",
#    icon="fa-rocket",
#    category="InterOp data",
#    category_icon="fa-cogs",
#)

appbuilder.add_view(
    IlluminaInteropDataView, "InterOp data", category_icon="fa-database", icon="fa-bar-chart", category="Sequencing runs"
)

appbuilder.add_view(
    PreDeMultiplexingDataView, "Pre de-multiplication", category_icon="fa-database", icon="fa-line-chart", category="Sequencing runs"
)


appbuilder.add_view_no_menu(TestPreDeMultiplexingDataView())

db.create_all()
