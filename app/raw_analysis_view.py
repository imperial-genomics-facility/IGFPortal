# import logging
# from io import BytesIO
# from . import db
# from .models import RawAnalysis
# from .models import RawAnalysisValidationSchema
# from .models import RawAnalysisTemplate
# from flask_appbuilder import ModelView
# from flask_appbuilder.models.sqla.filters import FilterInFunction
# from flask import redirect, flash, url_for, send_file
# from flask_appbuilder.actions import action
# from flask_appbuilder.models.sqla.interface import SQLAInterface
# from wtforms_sqlalchemy.fields import QuerySelectField
# from flask_appbuilder.fieldwidgets import Select2Widget
# from . import celery
# from .raw_analysis.raw_analysis_util import (
#     pipeline_query,
#     project_query,
#     validate_json_schema,
#     validate_analysis_design,
#     generate_analysis_template)

# log = logging.getLogger(__name__)

# class RawAnalysisTemplateView(ModelView):
#     datamodel = SQLAInterface(RawAnalysisTemplate)
#     label_columns = {
#         "template_tag": "Name",
#         "template_data": "Template"
#     }
#     base_permissions = [
#         "can_list",
#         "can_show",
#         "can_add",
#         "can_edit",
#         "can_delete"]
#     base_order = ("template_id", "desc")




# @celery.task(bind=True)
# def async_validate_analysis_schema(self, id_list):
#     try:
#         results = list()
#         for raw_analysis_schema_id in id_list:
#             msg = \
#                 validate_json_schema(
#                     raw_analysis_schema_id=raw_analysis_schema_id)
#             results.append(msg)
#         return dict(zip(id_list, results))
#     except Exception as e:
#         log.error(
#             f"Failed to run celery job, error: {e}")


# class RawAnalysisSchemaView(ModelView):
#     datamodel = SQLAInterface(RawAnalysisValidationSchema)
#     label_columns = {
#         "pipeline.pipeline_name": "Pipeline name",
#         "status": "Status",
#         "json_schema": "Schema"
#     }
#     list_columns = [
#         "pipeline.pipeline_name",
#         "status",
#         "date_stamp"]
#     show_columns = [
#         "pipeline.pipeline_name",
#         "status",
#         "date_stamp",
#         "json_schema"]
#     add_columns = [
#         "pipeline",
#         "json_schema"]
#     base_permissions = [
#         "can_list",
#         "can_show",
#         "can_add",
#         "can_delete"]
#     base_order = ("raw_analysis_schema_id", "desc")

#     add_form_extra_fields = {
#         "pipeline": QuerySelectField(
#             "Pipeline",
#             query_factory=pipeline_query,
#             widget=Select2Widget()
#         ),
#     }
#     edit_form_extra_fields = {
#         "pipeline": QuerySelectField(
#             "Pipeline",
#             query_factory=pipeline_query,
#             widget=Select2Widget()
#         )
#     }

#     @action("validate_json_analysis_schema", "Validate JSON", confirmation="Run validate?", multiple=True, single=False, icon="fa-rocket")
#     def validate_json_analysis_schema(self, item):
#         try:
#             id_list = list()
#             pipeline_list = list()
#             if isinstance(item, list):
#                 id_list = [i.raw_analysis_schema_id for i in item]
#                 pipeline_list = [i.pipeline.pipeline_name for i in item]
#             else:
#                 id_list = [item.raw_analysis_schema_id]
#                 pipeline_list = [item.pipeline.pipeline_name]
#             _ = \
#                 async_validate_analysis_schema.\
#                     apply_async(args=[id_list])
#             flash("Submitted jobs for {0}".format(', '.join(pipeline_list)), "info")
#             self.update_redirect()
#             return redirect(url_for('RawAnalysisSchemaView.list'))
#         except:
#             flash('Failed to validate analysis schema', 'danger')
#             return redirect(url_for('RawAnalysisSchemaView.list'))

#     @action("download_json_analysis_schema", "Download JSON schema", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def download_json_analysis_schema(self, item):
#         try:
#             json_schema = item.json_schema
#             if json_schema is None:
#                 json_schema = '{}'
#             output = BytesIO(json_schema.encode('utf-8'))
#             pipeline_name = item.pipeline.pipeline_name.encode('utf-8').decode()
#             output.seek(0)
#             self.update_redirect()
#             return send_file(output, download_name=f'{pipeline_name}_schema.json', as_attachment=True)
#         except:
#             flash('Failed to download analysis schema', 'danger')
#             return redirect(url_for('RawAnalysisSchemaView.list'))


# @celery.task(bind=True)
# def async_validate_analysis_yaml(self, id_list):
#     try:
#         results = list()
#         for raw_analysis_id in id_list:
#             msg = \
#                 validate_analysis_design(
#                     raw_analysis_id=raw_analysis_id)
#             results.append(msg)
#         return dict(zip(id_list, results))
#     except Exception as e:
#         log.error(
#             f"Failed to run celery job, error: {e}")

# def rename(newname):
#     def decorator(f):
#         f.__name__ = newname
#         return f
#     return decorator

# class RawAnalysisView(ModelView):
#     datamodel = SQLAInterface(RawAnalysis)
#     label_columns = {
#         "analysis_name": "Analysis name",
#         "project.project_igf_id": "Project name",
#         "pipeline.pipeline_name": "Pipeline name",
#         "status": "Status",
#         "date_stamp": "Updated on",
#         "analysis_yaml": "Yaml",
#         "report": "Report"}
#     list_columns = [
#         "analysis_name",
#         "project.project_igf_id",
#         "pipeline.pipeline_name",
#         "status",
#         "date_stamp"]
#     show_columns = [
#         "analysis_name",
#         "project.project_igf_id",
#         "pipeline.pipeline_name",
#         "status",
#         "date_stamp",
#         "analysis_yaml",
#         "report"]
#     add_columns = [
#         "analysis_name",
#         "project",
#         "pipeline",
#         "analysis_yaml"]
#     edit_columns = [
#         "analysis_name",
#         "project",
#         "pipeline",
#         "analysis_yaml"]
#     base_filters = [
#         ["status", FilterInFunction, lambda: ["UNKNOWN", "FAILED"]]]
#     base_order = ("raw_analysis_id", "desc")
#     base_permissions = [
#         "can_list",
#         "can_show",
#         "can_add",
#         "can_edit"]

#     add_form_extra_fields = {
#         "project": QuerySelectField(
#             "Project",
#             query_factory=project_query,
#             widget=Select2Widget()
#         ),
#         "pipeline": QuerySelectField(
#             "Pipeline",
#             query_factory=pipeline_query,
#             widget=Select2Widget()
#         ),
#     }
#     edit_form_extra_fields = {
#         "project": QuerySelectField(
#             "Project",
#             query_factory=project_query,
#             widget=Select2Widget()
#         ),
#         "pipeline": QuerySelectField(
#             "Pipeline",
#             query_factory=pipeline_query,
#             widget=Select2Widget()
#         )
#     }

#     @action("reject_raw_analysis", "Reject analysis", confirmation="Reject analysis design?", multiple=False, single=True, icon="fa-exclamation")
#     def reject_raw_analysis(self, item):
#         try:
#             if isinstance(item, list):
#                 try:
#                     for i in item:
#                         db.session.\
#                             query(RawAnalysis).\
#                             filter(RawAnalysis.raw_analysis_id==i.raw_analysis_id).\
#                             update({'status': 'REJECTED'})
#                     db.session.commit()
#                 except:
#                     db.session.rollback()
#                     raise
#             else:
#                 try:
#                     db.session.\
#                         query(RawAnalysis).\
#                         filter(RawAnalysis.raw_analysis_id==item.raw_analysis_id).\
#                         update({'status': 'REJECTED'})
#                     db.session.commit()
#                 except:
#                     db.session.rollback()
#                     raise
#             return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             log.error(e)
#             flash('Failed to reject analysis design', 'danger')
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("validate_and_submit_analysis", "Validate and upload analysis", confirmation="Validate analysis design?", multiple=True, single=False, icon="fa-rocket")
#     def validate_and_submit_analysis(self, item):
#         try:
#             analysis_list = list()
#             id_list = list()
#             if isinstance(item, list):
#                 analysis_list = [i.analysis_name for i in item]
#                 id_list = [i.raw_analysis_id for i in item]
#             else:
#                 analysis_list = [item.analysis_name]
#                 id_list = [item.raw_analysis_id]
#             _ = \
#                 async_validate_analysis_yaml.\
#                     apply_async(args=[id_list])
#             flash("Submitted jobs for {0}".format(', '.join(analysis_list)), "info")
#             self.update_redirect()
#             return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             log.error(e)
#             flash('Failed to validate analysis design', 'danger')
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("download_raw_analysis_damp", "Download analysis yaml", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def download_raw_analysis_damp(self, item):
#         try:
#             analysis_yaml = item.analysis_yaml
#             if analysis_yaml is None:
#                 analysis_yaml = ''
#             output = BytesIO(analysis_yaml.encode('utf-8'))
#             analysis_name = item.analysis_name.encode('utf-8').decode()
#             output.seek(0)
#             self.update_redirect()
#             return send_file(output, download_name=f"{analysis_name}_analysis.yaml", as_attachment=True)
#         except Exception as e:
#             flash('Failed to download raw analysis', 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_nf_rna", "Template NF_RNA", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_nf_rna(self, item):
#         try:
#             template_tag = "NF_RNA"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_sm_rna", "Template Snakemake_RNA", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_sm_rna(self, item):
#         try:
#             template_tag = "Snakemake_RNA"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_nf_smrna", "Template NF_smRNA", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_nf_smrna(self, item):
#         try:
#             template_tag = "NF_smRNA"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_nf_chip", "Template NF_ChIP", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_nf_chip(self, item):
#         try:
#             template_tag = "NF_ChIP"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_nf_atac", "Template NF_ATAC", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_nf_atac(self, item):
#         try:
#             template_tag  ="NF_ATAC"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_nf_hic", "Template NF_HI_C", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_nf_hic(self, item):
#         try:
#             template_tag = "NF_HI_C"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))


#     @action("template_nf_methylseq", "Template NF_Methylseq", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_nf_methylseq(self, item):
#         try:
#             template_tag = "NF_Methylseq"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))


#     @action("template_nf_sarek", "Template NF_Sarek", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_nf_sarek(self, item):
#         try:
#             template_tag = "NF_Sarek"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_nf_ampliseq", "Template NF_Ampliseq", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_nf_ampliseq(self, item):
#         try:
#             template_tag = "NF_Ampliseq"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_nf_cutandrun", "Template NF_CutAndRun", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_nf_cutandrun(self, item):
#         try:
#             template_tag = "NF_CutAndRun"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_nf_bactmap", "Template NF_BactMap", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_nf_bactmap(self, item):
#         try:
#             template_tag = "NF_BactMap"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_custom", "Template Custom", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_custom(self, item):
#         try:
#             template_tag = "Custom"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_geomx_dcc", "Template GeoMx dcc", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_geomx_dcc(self, item):
#         try:
#             template_tag = "GEOMX_DCC"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))

#     @action("template_cellranger_multi", "Template cellranger multi", confirmation=None, icon="fa-file-excel-o", multiple=False, single=True)
#     def template_cellranger_multi(self, item):
#         try:
#             template_tag = "CELLRANGER_MULTI"
#             if item.project_id is not None:
#                 formatted_template = \
#                     generate_analysis_template(
#                         project_igf_id=item.project.project_igf_id,
#                         template_tag=template_tag)
#                 output = BytesIO(formatted_template.encode('utf-8'))
#                 analysis_name = item.analysis_name.encode('utf-8').decode()
#                 output.seek(0)
#                 self.update_redirect()
#                 return send_file(output, download_name=f"{analysis_name}_{template_tag}_analysis.yaml", as_attachment=True)
#             else:
#                 flash(f"Failed to generate {template_tag} template, no project", 'danger')
#                 return redirect(url_for('RawAnalysisView.list'))
#         except Exception as e:
#             flash(f"Failed to generate {template_tag} template", 'danger')
#             log.error(e)
#             return redirect(url_for('RawAnalysisView.list'))


# class RawAnalysisQueueView(ModelView):
#     datamodel = SQLAInterface(RawAnalysis)
#     label_columns = {
#         "analysis_name": "Analysis name",
#         "project.project_igf_id": "Project name",
#         "pipeline.pipeline_name": "Pipeline name",
#         "status": "Status",
#         "date_stamp": "Updated on",
#         "analysis_yaml": "Yaml",
#         "report": "Report"
#     }
#     list_columns = [
#         "analysis_name",
#         "project.project_igf_id",
#         "pipeline.pipeline_name",
#         "status",
#         "date_stamp"]
#     show_columns = [
#         "analysis_name",
#         "project.project_igf_id",
#         "pipeline.pipeline_name",
#         "status",
#         "date_stamp",
#         "analysis_yaml", 
#         "report"]
#     base_filters = [
#         ["status", FilterInFunction, lambda: ["VALIDATED",]]]
#     base_order = ("raw_analysis_id", "desc")
#     base_permissions = [
#         "can_list",
#         "can_show"]