def test_admin_view(test_client):
    rv = test_client.get('/admin_home')
    assert rv.status_code == 302
    rv = test_client.get('/illuminainteropdataview/list/')
    assert rv.status_code == 302
    rv = test_client.get('/predemultiplexingdataview/list/')
    assert rv.status_code == 302
    rv = test_client.post("/login", data=dict(
            username='admin1',
            password='password'
            ), follow_redirects=True)
    assert rv.status_code == 200
    with test_client.session_transaction() as session:
        session['user_id'] = 1
        session['_fresh'] = True
    rv = test_client.get('/admin_home')
    assert rv.status_code == 200
    # rv = test_client.get('/illuminainteropdataview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/predemultiplexingdataview/list/')
    # assert rv.status_code == 200

# def test_view(test_client):
#     rv = test_client.get('/admin_home')
#     assert rv.status_code == 302
#     rv = test_client.get('/illuminainteropdataview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/predemultiplexingdataview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/samplesheetview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/rawseqrunview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/rawmetadatavalidationview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/rawmetadatasubmitview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/projectindexview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/sampleindexview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/rawanalysisview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/analysisview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/rdsprojectbackupview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/projectview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/sampleprojectview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/userview/list/')
#     assert rv.status_code == 302
#     rv = test_client.get('/seqrunview/list/')
#     assert rv.status_code == 302
#     rv = test_client.post("/login", data=dict(
#             username='admin',
#             password='password'
#             ), follow_redirects=True)
#     assert rv.status_code == 200
    # rv1 = test_client.get('/admin_home')
    # assert rv1.status_code == 200
    # rv = test_client.get('/illuminainteropdataview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/predemultiplexingdataview/list/')
    # assert rv.status_code == 201
    # rv = test_client.get('/samplesheetview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/rawseqrunview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/rawmetadatavalidationview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/rawmetadatasubmitview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/projectindexview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/sampleindexview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/rawanalysisview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/analysisview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/rdsprojectbackupview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/projectview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/sampleprojectview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/userview/list/')
    # assert rv.status_code == 200
    # rv = test_client.get('/seqrunview/list/')
    # assert rv.status_code == 200


# import os, unittest, time
# from flask_appbuilder import AppBuilder
# from app import db, app, appbuilder

# class TestApp1(unittest.TestCase):
#     def setUp(self):
#         app.config.update({
#             "TESTING": True,
#             "CSRF_ENABLED": False,
#             "SECRET_KEY": "thisismyscretkey",
#             "SQLALCHEMY_TRACK_MODIFICATIONS": False,
#             "WTF_CSRF_ENABLED": False,
#             "AUTH_ROLE_ADMIN": 'Admin',
#             "AUTH_USER_REGISTRATION_ROLE": "Admin",
#             "AUTH_ROLES_MAPPING": {
#                 "User": ["User"],
#                 "Admin": ["admin"],
#             },
#             "SQLALCHEMY_DATABASE_URI": "sqlite:////tmp/app2.db",
#         })
#         print(db.get_engine().url)
#         db.create_all()
#         print(db.session.is_active)
#         # db.drop_all()
#         #appbuilder#.init_app(app, db.session)
#         # db.create_all()
#         # app
#         print(db.get_engine().url)
#         role_admin = \
#             app.appbuilder.sm.find_role("Admin")
#         print(role_admin)
#         self.assertIsNotNone(role_admin)
#         user = app.appbuilder.sm.find_user(email="admin@fab.org")
#         if user is None:
#             app.appbuilder.sm.add_user(
#                 "admin",
#                 "admin",
#                 "user",
#                 "admin@fab.org",
#                 role_admin,
#                 "password")
#         self.app_context = app.app_context()
#         self.app_context.push()
#         self.client = app.test_client(use_cookies=False)


#     def tearDown(self):
#         db.session.remove()
#         self.app_context.pop()
#         db.drop_all()
#         if os.path.exists("/tmp/app2.db"):
#             os.remove("/tmp/app2.db")


#     def test_server_access_without_login(self):
#         rv2 = self.client.get('/admin_home')
#         self.assertEqual(rv2.status_code, 302)
#         rv3 = self.client.get('/illuminainteropdataview/list/')
#         self.assertEqual(rv3.status_code, 302)
#         rv4 = self.client.get('/predemultiplexingdataview/list/')
#         self.assertEqual(rv4.status_code, 302)
#         rv5 = self.client.get('/samplesheetview/list/')
#         self.assertEqual(rv5.status_code, 302)
#         rv6 = self.client.get('/rawseqrunview/list/')
#         self.assertEqual(rv6.status_code, 302)
#         rv7 = self.client.get('/rawmetadatavalidationview/list/')
#         self.assertEqual(rv7.status_code, 302)
#         rv8 = self.client.get('/rawmetadatasubmitview/list/')
#         self.assertEqual(rv8.status_code, 302)
#         rv9 = self.client.get('/projectindexview/list/')
#         self.assertEqual(rv9.status_code, 302)
#         rv10 = self.client.get('/sampleindexview/list/')
#         self.assertEqual(rv10.status_code, 302)
#         rv11 = self.client.get('/rawanalysisview/list/')
#         self.assertEqual(rv11.status_code, 302)
#         rv12 = self.client.get('/analysisview/list/')
#         self.assertEqual(rv12.status_code, 302)
#         rv13 = self.client.get('/rdsprojectbackupview/list/')
#         self.assertEqual(rv13.status_code, 302)
#         rv14 = self.client.get('/projectview/list/')
#         self.assertEqual(rv14.status_code, 302)
#         rv15 = self.client.get('/sampleprojectview/list/')
#         self.assertEqual(rv15.status_code, 302)
#         rv16 = self.client.get('/userview/list/')
#         self.assertEqual(rv16.status_code, 302)
#         rv17 = self.client.get('/seqrunview/list/')
#         self.assertEqual(rv17.status_code, 302)
#         rv8 = self.client.post("/login", data=dict(
#             username='admin',
#             password='password'
#             ), follow_redirects=True)
#         self.assertEqual(rv8.status_code, 200)
#         rv9 = self.client.get('/admin_home')
#         self.assertEqual(rv9.status_code, 200)
#         rv10 = self.client.get('/illuminainteropdataview/list/')
#         self.assertEqual(rv10.status_code, 200)

# class TestApp2(unittest.TestCase):
#     def setUp(self):
#         db.drop_all()
#         os.environ['SQLALCHEMY_DATABASE_URI'] = "sqlite:////tmp/app4.db"
#         app.config.update({
#             "TESTING": True,
#             "CSRF_ENABLED": False,
#         })
#         self.app_context = app.app_context()
#         self.app_context.push()
#         db.create_all()
#         app.config.from_object("flask_appbuilder.tests.config_api")
#         self.client = app.test_client(use_cookies=True)
#         role_admin = \
#             app.appbuilder.sm.find_role(
#                 app.appbuilder.sm.auth_role_admin)
#         app.appbuilder.sm.add_user(
#             "admin",
#             "admin",
#             "user",
#             "admin@fab.org",
#             role_admin,
#             "password")


#     def tearDown(self):
#         db.session.remove()
#         self.app_context.pop()
#         db.drop_all()

#     def test_access_server(self):
#         rv = self.client.post("/login", data=dict(
#             username='admin',
#             password='password'
#             ), follow_redirects=True)
#         self.assertEqual(rv.status_code, 200)
#         rv2 = self.client.get('/admin_home')
#         self.assertEqual(rv2.status_code, 200)
#         rv3 = self.client.get('/illuminainteropdataview/list/')
#         self.assertEqual(rv3.status_code, 200)
#         rv5 = self.client.get('/samplesheetview/list/')
#         self.assertEqual(rv5.status_code, 200)
#         rv6 = self.client.get('/rawseqrunview/list/')
#         self.assertEqual(rv6.status_code, 200)
#         rv7 = self.client.get('/rawmetadatavalidationview/list/')
#         self.assertEqual(rv7.status_code, 200)
#         rv8 = self.client.get('/rawmetadatasubmitview/list/')
#         self.assertEqual(rv8.status_code, 200)
#         rv9 = self.client.get('/projectindexview/list/')
#         self.assertEqual(rv9.status_code, 200)
#         rv10 = self.client.get('/sampleindexview/list/')
#         self.assertEqual(rv10.status_code, 200)
#         rv11 = self.client.get('/rawanalysisview/list/')
#         self.assertEqual(rv11.status_code, 200)
#         rv12 = self.client.get('/analysisview/list/')
#         self.assertEqual(rv12.status_code, 200)
#         rv13 = self.client.get('/rdsprojectbackupview/list/')
#         self.assertEqual(rv13.status_code, 200)
#         rv14 = self.client.get('/projectview/list/')
#         self.assertEqual(rv14.status_code, 200)
#         rv15 = self.client.get('/sampleprojectview/list/')
#         self.assertEqual(rv15.status_code, 200)
#         rv16 = self.client.get('/userview/list/')
#         self.assertEqual(rv16.status_code, 200)
#         rv17 = self.client.get('/seqrunview/list/')
#         self.assertEqual(rv17.status_code, 200)

# if __name__ == '__main__':
#   unittest.main()