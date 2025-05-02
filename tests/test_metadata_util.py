import os, unittest, json, tempfile
# from app import appbuilder, db
from app.models import (
    Project,
    Sample,
    IgfUser,
    Pipeline,
    Platform,
    Seqrun,
    Analysis,
    RawAnalysis,
    RawAnalysisValidationSchema,
    RawAnalysisTemplate,
    Project_info_data,
    Project_seqrun_info_data,
    Project_seqrun_info_file,
    Project_analysis_info_data,
    Project_analysis_info_file)
from app.metadata.metadata_util import (
    backup_specific_portal_tables,
    cleanup_and_load_new_data_to_metadata_tables,
    check_for_projects_in_metadata_db,
    check_sample_and_project_ids_in_metadata_db,
    check_user_name_and_email_in_metadata_db)

def test_backup_specific_portal_tables(db, tmp_path):
    project3 = \
        Project(
            project_id=3,
            project_igf_id="test3")
    ## add raw analysis before loading new data
    pipeline = \
        Pipeline(
            pipeline_name="pipeline1",
            pipeline_db="",
            pipeline_type='AIRFLOW')
    raw_analysis = \
        RawAnalysis(
            analysis_name="analysis1",
            analysis_yaml="test",
            status="VALIDATED",
            project=project3,
            pipeline=pipeline)
    try:
        db.session.add(project3)
        db.session.add(pipeline)
        db.session.add(raw_analysis)
        db.session.flush()
        db.session.commit()
    except:
        db.session.rollback()
        raise
    result = \
        db.session.\
            query(RawAnalysis).\
            filter(RawAnalysis.analysis_name=="analysis1").\
            one_or_none()
    assert result is not None
    assert result.raw_analysis_id == 1
    assert result.project_id == 3
    (_, json_file) = \
        tempfile.mkstemp(
            dir=tmp_path,
            suffix='.json',
            prefix='portal_metadata_',)
    assert os.path.exists(json_file)
    json_file = \
        backup_specific_portal_tables(json_file)
    assert os.path.exists(json_file)
    with open(json_file, 'r') as fp:
        json_data = json.load(fp)
    assert 'raw_analysis' in json_data
    raw_analysis_data = \
        json_data.get('raw_analysis')
    assert isinstance(raw_analysis_data, list)
    assert len(raw_analysis_data) == 1
    assert 'analysis_name' in raw_analysis_data[0]
    assert raw_analysis_data[0].get('analysis_name') == 'analysis1'
    result = \
        db.session.\
            query(RawAnalysis).\
            filter(RawAnalysis.analysis_name=="analysis1").\
            one_or_none()
    assert result is not None
    assert result.raw_analysis_id == 1
    assert result.project_id == 3


# class TestMetadataUtil1(unittest.TestCase):
#     def setUp(self):
#         # db.drop_all()
#         # if os.path.exists('/tmp/app.db'):
#         #     os.remove('/tmp/app.db')
#         db.create_all()

#     def tearDown(self):
#         db.session.remove()
#         db.drop_all()

def test_cleanup_and_load_new_data_to_metadata_tables(db, tmp_path):
    # def test_cleanup_and_load_new_data_to_metadata_tables(self):
        project2 = \
            Project(
                project_id=2,
                project_igf_id="test2")
        project3 = \
            Project(
                project_id=3,
                project_igf_id="test3")
        ## add raw analysis before loading new data
        pipeline = \
            Pipeline(
                pipeline_id=1,
                pipeline_name="pipeline1",
                pipeline_db="",
                pipeline_type='AIRFLOW'
            )
        raw_analysis = \
            RawAnalysis(
                raw_analysis_id=1,
                analysis_name="analysis1",
                analysis_yaml="test",
                status="VALIDATED",
                project=project3,
                pipeline=pipeline
            )
        raw_validation_schema = \
            RawAnalysisValidationSchema(
                raw_analysis_schema_id=1,
                pipeline=pipeline,
                json_schema="",
                status="VALIDATED")
        raw_analysis_template = \
            RawAnalysisTemplate(
                template_id=1,
                template_tag="test",
                template_data="test")
        platform = \
            Platform(
                platform_id=1,
                platform_igf_id="test_platform",
                model_name="NOVASEQ6000",
                vendor_name="ILLUMINA",
                software_name="RTA")
        seqrun = \
            Seqrun(
                seqrun_id=1,
                seqrun_igf_id="test_seqrun",
                flowcell_id="FLOWCELL1",
                platform=platform)
        analysis = \
            Analysis(
                analysis_id=1,
                project=project3,
                analysis_name="test_analysis",
                analysis_type="test_analysis_type")
        project_info_data = \
            Project_info_data(
                project_info_data_id=1,
                sample_read_count_data="test",
                project_history_data="test",
                project=project3)
        project_seqrun_info_data = \
            Project_seqrun_info_data(
                project_seqrun_info_data_id=1,
                project=project3,
                seqrun=seqrun,
                lane_number='1',
                index_group_tag="test_ig",
                project_info_data=project_info_data)
        project_seqrun_info_file = \
            Project_seqrun_info_file(
                project_seqrun_info_file_id=1,
                project_seqrun_info_data=project_seqrun_info_data,
                file_path="test")
        project_analysis_info_data = \
            Project_analysis_info_data(
                project_analysis_info_data_id=1,
                project=project3,
                analysis=analysis,
                analysis_tag="test_analysis_tag",
                project_info_data=project_info_data)
        project_analysis_info_file = \
            Project_analysis_info_file(
                project_analysis_info_file_id=1,
                project_analysis_info_data=project_analysis_info_data,
                file_path="test")
        try:
            db.session.add(project2)
            db.session.add(project3)
            db.session.add(pipeline)
            db.session.add(raw_analysis)
            db.session.add(raw_validation_schema)
            db.session.add(raw_analysis_template)
            db.session.add(platform)
            db.session.add(seqrun)
            db.session.add(analysis)
            db.session.add(project_info_data)
            db.session.add(project_seqrun_info_data)
            db.session.add(project_seqrun_info_file)
            db.session.add(project_analysis_info_data)
            db.session.add(project_analysis_info_file)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        result = \
            db.session.\
                query(Project).\
                filter(Project.project_igf_id=="test2").\
                one_or_none()
        assert result is not None
        assert result.project_id == 2
        json_data = {
            "project": [{
                "project_id": 1,
                "project_igf_id": "test1"},{
                "project_id": 3,
                "project_igf_id": "test3"}],
            "pipeline": [{
                "pipeline_id": 1,
                "pipeline_name": "pipeline1",
                "pipeline_db": "",
                "pipeline_type": "AIRFLOW"}],
            "analysis": [dict(
                analysis_id=1,
                project_id=3,
                analysis_name="test_analysis",
                analysis_type="test_analysis_type")],
            "platform": [dict(
                platform_id=1,
                platform_igf_id="test_platform",
                model_name="NOVASEQ6000",
                vendor_name="ILLUMINA",
                software_name="RTA")],
            "seqrun": [dict(
                seqrun_id=1,
                seqrun_igf_id="test_seqrun",
                flowcell_id="FLOWCELL1",
                platform_id=1)]}
        temp_json_file = \
            os.path.join(tmp_path, 'metadata_db.json')
        with open(temp_json_file, 'w') as fp:
            json.dump(json_data, fp)
        cleanup_and_load_new_data_to_metadata_tables(temp_json_file)
        result = \
            db.session.\
                query(Project).\
                filter(Project.project_igf_id=="test1").\
                one_or_none()
        assert result is not None
        assert result.project_id == 1
        result = \
            db.session.\
                query(Project).\
                filter(Project.project_igf_id=="test2").\
                one_or_none()
        assert result is None
        result = \
            db.session.\
                query(RawAnalysis).\
                filter(RawAnalysis.analysis_name=="analysis1").\
                one_or_none()
        assert result is not None
        assert result.analysis_name == "analysis1"
        assert result.project_id == 3
        assert result.pipeline_id == 1
        result = \
            db.session.\
                query(Project_info_data).\
                filter(Project_info_data.project_info_data_id==1).\
                one_or_none()
        assert result is not None
        assert result.sample_read_count_data == "test"
        assert result.project_id == 3
        result = \
            db.session.\
                query(Project_seqrun_info_data).\
                filter(Project_seqrun_info_data.project_seqrun_info_data_id==1).\
                one_or_none()
        assert result is not None
        assert result.project_id == 3
        assert result.project_info_data_id == 1
        result = \
            db.session.\
                query(Project_seqrun_info_file).\
                filter(Project_seqrun_info_file.project_seqrun_info_file_id==1).\
                one_or_none()
        assert result is not None
        assert result.project_seqrun_info_data_id == 1
        assert result.file_path == "test"
        result = \
            db.session.\
                query(Project_analysis_info_data).\
                filter(Project_analysis_info_data.project_analysis_info_data_id==1).\
                one_or_none()
        assert result is not None
        assert result.analysis_tag == "test_analysis_tag"
        assert result.analysis_id == 1
        result = \
            db.session.\
                query(Project_analysis_info_file).\
                filter(Project_analysis_info_file.project_analysis_info_file_id==1).\
                one_or_none()
        assert result is not None
        assert result.file_path == "test"



# class TestMetadataUtil2(unittest.TestCase):
#     def setUp(self):
#         db.create_all()

#     def tearDown(self):
#         db.drop_all()

def test_check_for_projects_in_metadata_db(db, tmp_path):
    # def test_check_for_projects_in_metadata_db(self):
        project = \
            Project(
                project_id=1,
                project_igf_id="test11")
        try:
            db.session.add(project)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        result = \
            db.session.\
                query(Project).\
                filter(Project.project_igf_id=="test11").\
                one_or_none()
        # self.assertTrue(result is not None)
        # self.assertEqual(result.project_id, 1)
        assert result is not None
        assert result.project_id == 1
        output, errors = \
            check_for_projects_in_metadata_db(project_list=["test11", "test12"])
        # self.assertTrue(output.get('test11'))
        # self.assertFalse(output.get('test12'))
        # self.assertEqual(len(errors), 1)
        assert output.get('test11') is not None
        assert len(errors) == 1
        output, errors = \
            check_for_projects_in_metadata_db(
                project_list=["test11", "test12"],
                flag_existing_project=True)
        # self.assertTrue(output.get('test11'))
        # self.assertFalse(output.get('test12'))
        # self.assertEqual(len(errors), 1)
        assert output.get('test11') is not None
        assert len(errors) == 1

# class TestMetadataUtil3(unittest.TestCase):
#     def setUp(self):
#         db.drop_all()
#         db.create_all()

#     def tearDown(self):
#         db.drop_all()

def test_check_sample_and_project_ids_in_metadata_db(db, tmp_path):
    # def test_check_sample_and_project_ids_in_metadata_db(self):
        project1 = \
            Project(
                project_id=1,
                project_igf_id="test1")
        project2 = \
            Project(
                project_id=2,
                project_igf_id="test2")
        sample1 = \
            Sample(
                sample_id=1,
                sample_igf_id='test_sample1',
                project_id=1)
        sample2 = \
            Sample(
                sample_id=2,
                sample_igf_id='test_sample2',
                project_id=2)
        try:
            db.session.add(project1)
            db.session.add(project2)
            db.session.add(sample1)
            db.session.add(sample2)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        sample_project_list = [{
            'sample_igf_id':'test_sample1',
            'project_igf_id':'test1',
            'name':'',
            'email_id':''},{
            'sample_igf_id':'test_sample2',
            'project_igf_id':'test1',
            'name':'',
            'email_id':''},{
            'sample_igf_id':'test_sample3',
            'project_igf_id':'test1',
            'name':'',
            'email_id':''}]
        errors = \
            check_sample_and_project_ids_in_metadata_db(
                sample_project_list)
        # self.assertTrue('Missing metadata for sample test_sample3' in errors)
        # self.assertTrue("Sample test_sample2 is linked to project test2, not test1" in errors)
        assert 'Missing metadata for sample test_sample3' in errors
        assert "Sample test_sample2 is linked to project test2, not test1" in errors

def test_check_user_name_and_email_in_metadata_db(db, tmp_path):
    # def test_check_user_name_and_email_in_metadata_db(self):
        user = \
            IgfUser(
                name='User A',
                email_id='a@g.com')
        try:
            db.session.add(user)
            db.session.flush()
            db.session.commit()
        except:
            db.session.rollback()
            raise
        data1 = [{'name':'User B', 'email_id': 'b@g.com'}]
        errors = \
            check_user_name_and_email_in_metadata_db(data1)
        # self.assertTrue('Missing name User B in db' in errors)
        # self.assertTrue('Missing email b@g.com in db' in errors)
        assert 'Missing name User B in db' in errors
        assert 'Missing email b@g.com in db' in errors
        data1 = [{'name':'User A', 'email_id': 'a@g.com'}]
        errors = \
            check_user_name_and_email_in_metadata_db(data1)
        # self.assertEqual(len(errors), 0)
        assert len(errors) == 0
        data1 = [{'name':'User B', 'email_id': 'a@g.com'}]
        errors = \
            check_user_name_and_email_in_metadata_db(data1)
        # self.assertTrue('Missing name User B in db' in errors)
        # self.assertTrue("Email a@g.com registered with name User A, not User B" in errors)
        assert 'Missing name User B in db' in errors
        assert "Email a@g.com registered with name User A, not User B" in errors
        data1 = [{'name':'User A', 'email_id': 'b@g.com'}]
        errors = \
            check_user_name_and_email_in_metadata_db(data1)
        # self.assertTrue('Missing email b@g.com in db' in errors)
        # self.assertTrue("User User A registered with email id a@g.com, not b@g.com" in errors)
        assert 'Missing email b@g.com in db' in errors
        assert "User User A registered with email id a@g.com, not b@g.com" in errors
        data1 = [{'name':'User B', 'email_id': 'b@g.com'}]
        errors = \
            check_user_name_and_email_in_metadata_db(
                name_email_list=data1,
                check_missing=False)
        # self.assertEqual(len(errors), 0)
        assert len(errors) == 0

# if __name__ == '__main__':
#   unittest.main()