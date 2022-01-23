import unittest

def get_tests():
    return full_suite()

def full_suite():
    # import statements
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(t)
        for t in [
            ]
    ])