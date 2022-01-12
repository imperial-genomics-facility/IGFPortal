import json
from flask import render_template, redirect, flash, url_for, send_file, abort
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi, SimpleFormView
from flask_appbuilder.baseviews import BaseView, expose
from . import appbuilder, db
from .models import IlluminaInteropData
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

class IlluminaInteropDataView(ModelView):
    datamodel = SQLAInterface(IlluminaInteropData)


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

appbuilder.add_view(
    SeqrunInteropFormView,
    "Search sequencing run",
    icon="fa-rocket",
    category="InterOp data",
    category_icon="fa-cogs",
)

appbuilder.add_view(
    IlluminaInteropDataView, "IlluminaInteropDataView", icon="fa-folder-open-o", category="InterOp data"
)


db.create_all()
