import logging
from flask_appbuilder.baseviews import BaseView, expose
from flask_appbuilder.security.decorators import protect, has_access
from . import db
from .models import AdminHomeData


"""
    Home view
"""

def fetch_admin_home_data():
    try:
        results = \
            db.session.\
            query(AdminHomeData).\
            filter(AdminHomeData.admin_data_tag=="production_data").\
            all()
        if len(results) > 0:
            finished_seqrun = results[0].recent_finished_runs
            finished_analysis = results[0].recent_finished_analysis
            ongoing_seqrun = results[0].ongoing_runs
            ongoing_analysis = results[0].ongoing_analysis
            data1 = results[0].sequence_counts_plot
            data2 = results[0].storage_stat_plot
        else:
            finished_seqrun = ""
            finished_analysis = ""
            ongoing_seqrun = ""
            ongoing_analysis = ""
            data1 = ""
            data2 = ""
        return finished_seqrun, finished_analysis, ongoing_seqrun, ongoing_analysis, data1, data2
    except Exception as e:
        logging.error(e)


class HomeView(BaseView):
    route_base = "/"

    @expose('/user_home')
    @has_access
    def general(self):
        return self.render_template('user_index.html')

    @expose('/admin_home')
    @has_access
    def admin_home(self):
        (finished_seqrun, finished_analysis,
         ongoing_seqrun, ongoing_analysis,
         data1, data2) = \
            fetch_admin_home_data()
        return self.render_template(
                'admin_index.html',
                data1=data1,
                data2=data2,
                finished_seqrun=finished_seqrun,
                finished_analysis=finished_analysis,
                ongoing_seqrun=ongoing_seqrun,
                ongoing_analysis=ongoing_analysis)
