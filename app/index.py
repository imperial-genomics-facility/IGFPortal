from flask import Flask, redirect, g, url_for
from flask_appbuilder.baseviews import expose
from flask_appbuilder import IndexView, BaseView

class CustomIndexView(IndexView):
    #index_template = 'index.html'
    @expose('/')
    def index(self):
        user = g.user
        if user.is_anonymous:
            return redirect(url_for('AuthDBView.login'))
        elif user.username == "admin":
            return redirect(url_for('HomeView.admin_home'))
        else:
            return redirect(url_for('HomeView.general'))