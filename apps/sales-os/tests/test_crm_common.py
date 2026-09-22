import os
import sys
import unittest
from unittest.mock import MagicMock

# Mock google modules before crm_common is imported if google is not installed
sys.modules['google'] = MagicMock()
sys.modules['google.oauth2'] = MagicMock()
sys.modules['google.oauth2.credentials'] = MagicMock()
sys.modules['googleapiclient'] = MagicMock()
sys.modules['googleapiclient.discovery'] = MagicMock()

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../engine/operator_layer")))

from crm_common import col

class TestCrmCommonCol(unittest.TestCase):
    def test_col_basic_index_to_letter(self):
        self.assertEqual(col(0), "A")
        self.assertEqual(col(1), "B")
        self.assertEqual(col(25), "Z")

    def test_col_double_letters(self):
        self.assertEqual(col(26), "AA")
        self.assertEqual(col(27), "AB")
        self.assertEqual(col(51), "AZ")
        self.assertEqual(col(52), "BA")
        self.assertEqual(col(701), "ZZ")

    def test_col_triple_letters(self):
        self.assertEqual(col(702), "AAA")
        self.assertEqual(col(703), "AAB")

if __name__ == "__main__":
    unittest.main()
