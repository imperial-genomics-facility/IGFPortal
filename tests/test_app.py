import os, unittest, time
from app import app, db, appbuilder
from flask import Flask, g, url_for


class TestCase1(unittest.TestCase):
    def setUp(self):
        # if os.path.exists('app.db'):
        #     os.remove('app.db')
        self.app_context = app.app_context()
        self.app_context.push()
        app.config.update({
            "TESTING": True,
        })
        app.config.from_object("flask_appbuilder.tests.config_api")
        db.create_all()
        self.client = app.test_client(use_cookies=True)
        role_admin = \
            app.appbuilder.sm.find_role(
                app.appbuilder.sm.auth_role_admin)
        app.appbuilder.sm.add_user(
            "admin",
            "admin",
            "user",
            "admin@fab.org",
            role_admin,
            "password")


    def tearDown(self):
        db.session.remove()
        self.app_context.pop()
        db.drop_all()
        if os.path.exists('app.db'):
           os.remove('app.db')

    def test_access_server(self):
        uri = "/login"
        rv = self.client.post(uri, data=dict(
            username='admin',
            password='password'
            ), follow_redirects=True)
        self.assertEqual(rv.status_code, 200)





if __name__ == '__main__':
  unittest.main()