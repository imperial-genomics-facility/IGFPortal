from flask_appbuilder import BaseView, expose, has_access
import pandas as pd
from . import appbuilder

class PipelineTriggerView(BaseView):
    route_base = "/"
    @expose("/trigger_page")
    @has_access
    def trigger_page(self):
        pipeline_table = [
            ['Fin', '<a href="/admin_home" class="btn btn-primary btn active" role="button" aria-pressed="true">Trigger pipeline</a>'],
            ['Pipeline 2', '<a href="/admin_home" class="btn btn-primary btn active" role="button" aria-pressed="true">Trigger pipeline</a>']
        ]
        return self.render_template("pipeline_trigger.html", pipeline_table=pipeline_table)