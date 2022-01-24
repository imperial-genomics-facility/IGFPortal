import unittest

def get_tests():
    return full_suite()

def full_suite():
    # import statements
    from .test_apis import TestApiCase
    from .test_pre_demultiplexing_view import TestPreDemultView
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(t)
            for t in [
                TestApiCase,
                TestPreDemultView
            ]
    ])