import base, unittest

import yacpdb.indexer.metadata

stor = yacpdb.indexer.metadata.PredicateStorage('./')

class TestHma(unittest.TestCase):

    def test_ExistingId(self):
        pass