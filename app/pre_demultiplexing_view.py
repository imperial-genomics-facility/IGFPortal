import logging
from typing import Any
from io import BytesIO
from app import cache
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView
from flask_appbuilder.baseviews import expose
from flask import redirect, flash, url_for, send_file
from flask_appbuilder.security.decorators import has_access
from . import db
from .models import PreDeMultiplexingData

log = logging.getLogger(__name__)

"""
    Pre de-multiplexing view
"""

class PreDeMultiplexingDataView(ModelView):
    datamodel = SQLAInterface(PreDeMultiplexingData)
    label_columns = {
        'run_name':'Sequencing run',
        'samplesheet_tag':'Tag',
        'date_stamp': 'Updated on',
        'report': 'Report',
        'download_report': 'Download'}
    list_columns = [
        'run_name',
        'samplesheet_tag',
        'date_stamp',
        'report',
        'download_report']
    base_permissions = ['can_list', 'can_download_reports']#, 'can_get_report']
    base_order = ("date_stamp", "desc")

    @expose("/download/rawdata/<int:id>")
    @has_access
    @cache.cached(timeout=600)
    def download_reports(self, id: str) -> Any:
        try:
            records = \
                db.session.\
                query(
                    PreDeMultiplexingData.samplesheet_tag,
                    PreDeMultiplexingData.file_path).\
                filter(PreDeMultiplexingData.demult_id==id).\
                one_or_none()
            if records is None:
                raise ValueError(f"Report not found for id: {id}")
            (sample_sheet_tag, file_path) = records
            with open(file_path, 'rb') as fp:
                html_data = fp.read()
            output = BytesIO(html_data)
            sample_sheet_tag = sample_sheet_tag.encode('utf-8').decode()
            output.seek(0)
            self.update_redirect()
            return send_file(output, download_name=f'{sample_sheet_tag}.html', as_attachment=True)
        except Exception as e:
            log.error(e)
            flash('Failed to download report', 'danger')
            return redirect(url_for('PreDeMultiplexingDataView.list'))

    # @expose('/predemult_report/<int:id>')
    # @has_access
    # @cache.cached(timeout=600)
    # def get_report(self, id):
    #     try:
    #         (run_name, samplesheet_tag, flowcell_cluster_plot, project_summary_table, project_summary_plot,
    #          sample_table, sample_plot, undetermined_table, undetermined_plot, date_stamp) = \
    #             get_pre_demultiplexing_data(demult_id=id)
    #         flowcell_labels = flowcell_cluster_plot.get('labels')
    #         total_cluster_raw = flowcell_cluster_plot.get('total_cluster_raw')
    #         total_cluster_pf = flowcell_cluster_plot.get('total_cluster_pf')
    #         total_yield = flowcell_cluster_plot.get('total_yield')
    #         lanes = list(sample_table.keys())
    #         return \
    #         self.render_template(
    #             'demultiplexing_report.html',
    #             run_name=run_name,
    #             date_stamp=date_stamp,
    #             flowcell_labels=flowcell_labels,
    #             total_cluster_raw=total_cluster_raw,
    #             total_cluster_pf=total_cluster_pf,
    #             total_yield=total_yield,
    #             project_summary_table=project_summary_table,
    #             project_summary_plot=project_summary_plot,
    #             sample_table=sample_table,
    #             sample_plot=sample_plot,
    #             undetermined_table=undetermined_table,
    #             undetermined_plot=undetermined_plot,
    #             lanes=lanes)
    #     except Exception as e:
    #         log.error(e)


# def get_pre_demultiplexing_data(demult_id):
#     try:
#         result = \
#             db.session.\
#             query(PreDeMultiplexingData).\
#             filter(PreDeMultiplexingData.demult_id==demult_id).\
#             one_or_none()
#         run_name = ''
#         samplesheet_tag = ''
#         flowcell_cluster_plot = ''
#         project_summary_table = ''
#         project_summary_plot = ''
#         sample_table = ''
#         undetermined_table = ''
#         undetermined_plot = ''
#         if result is not None:
#             run_name = result.run_name
#             samplesheet_tag = result.samplesheet_tag
#             flowcell_cluster_plot = result.flowcell_cluster_plot
#             if isinstance(flowcell_cluster_plot, str):
#                 flowcell_cluster_plot = json.loads(flowcell_cluster_plot)
#             project_summary_table = result.project_summary_table
#             project_summary_plot = result.project_summary_plot
#             if isinstance(project_summary_plot, str):
#                 project_summary_plot = json.loads(project_summary_plot)
#             sample_table = result.sample_table
#             if isinstance(sample_table, str):
#                 sample_table = json.loads(sample_table)
#             sample_plot = result.sample_plot
#             if isinstance(sample_plot, str):
#                 sample_plot = json.loads(sample_plot)
#             undetermined_table = result.undetermined_table
#             if isinstance(undetermined_table, str):
#                 undetermined_table = json.loads(undetermined_table)
#             undetermined_plot = result.undetermined_plot
#             if isinstance(undetermined_plot, str):
#                 undetermined_plot = json.loads(undetermined_plot)
#             date_stamp = result.date_stamp
#         return run_name, samplesheet_tag, flowcell_cluster_plot, project_summary_table, project_summary_plot,\
#                sample_table, sample_plot, undetermined_table, undetermined_plot, date_stamp
#     except:
#         raise