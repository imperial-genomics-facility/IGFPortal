import unittest

def get_tests():
    return full_suite()

def full_suite():
    # import statements
    from .test_apis import TestApiCase
    from .test_pre_demultiplexing_view import TestPreDemultView
    from .test_samplesheet_util import TestSampleSheetUtil, TestSampleSheetDbUpdate
    from .test_raw_metadata_util import TestMetaDataValidation1, TestMetaDataValidation2
    from .test_metadata_util import TestMetadataUtil1, TestMetadataUtil2
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(t)
            for t in [
                TestApiCase,
                TestPreDemultView,
                TestSampleSheetUtil,
                TestSampleSheetDbUpdate,
                TestMetaDataValidation1,
                TestMetaDataValidation2,
                TestMetadataUtil1,
                TestMetadataUtil2
            ]
    ])