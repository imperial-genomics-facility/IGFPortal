import unittest

def get_tests():
    return full_suite()

def full_suite():
    # import statements
    from .test_apis import TestApiCase
    return unittest.TestSuite([
        unittest.TestLoader().loadTestsFromTestCase(t)
            for t in [
                TestApiCase
            ]
    ])