import unittest
import validate
import tests.unit.data

class TestDummy(unittest.TestCase):

    def test(self):
        self.assertTrue(True)

    def test_CanHandleReciStipulation(self):
        validate.validateStipulation(tests.unit.data.problems['reci-h#']['stipulation'])
