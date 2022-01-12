from flask import render_template
from flask_appbuilder.models.sqla.interface import SQLAInterface
from flask_appbuilder import ModelView, ModelRestApi
from flask_appbuilder.baseviews import BaseView, expose

from . import appbuilder, db

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


db.create_all()
