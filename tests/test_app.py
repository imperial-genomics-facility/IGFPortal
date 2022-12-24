import os, unittest, tempfile
from flask.testing import FlaskClient
from app import app, db, appbuilder
from flask import Flask, g, url_for


class TestCase1(unittest.TestCase):
    def setUp(self):
        app.app_context().push()
        app.config.from_object("flask_appbuilder.tests.config_api")
        db.create_all()
        self.client = app.test_client(use_cookies=True)
        app.appbuilder.sm.add_user(
            "admin",
            "admin",
            "user",
            "admin@fab.org",
            "Admin",
            "password")


    def tearDown(self):
        self.appbuilder = None
        db.drop_all()

    def test_access_server(self):
        uri = "/"
        rv = self.client.get(uri)
        #self.assertEqual(rv.status_code, 200)
        print(rv.status_code)




if __name__ == '__main__':
  unittest.main()