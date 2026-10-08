import tempfile
import unittest
from decimal import Decimal
from pathlib import Path
from reconciliation.core import Record, category_totals, compare, load_records


class ReconciliationTests(unittest.TestCase):
    def setUp(self):
        self.reference = {'1': Record('1', 'A', Decimal('10.00'), '2026-01-01T00:00:00Z')}

    def test_identical_data_passes(self):
        self.assertTrue(compare(self.reference, dict(self.reference))['summary']['passed'])

    def test_missing_and_unexpected_records(self):
        result = compare(self.reference, {'2': Record('2', 'A', Decimal('4'), '2026-01-01T00:00:00Z')})
        self.assertEqual(result['missing_ids'], ['1'])
        self.assertEqual(result['unexpected_ids'], ['2'])
        self.assertFalse(result['summary']['passed'])

    def test_tolerance(self):
        actual = {'1': Record('1', 'A', Decimal('10.01'), '2026-01-01T00:00:00Z')}
        self.assertTrue(compare(self.reference, actual)['summary']['passed'])
        actual['1'] = Record('1', 'A', Decimal('10.02'), '2026-01-01T00:00:00Z')
        self.assertFalse(compare(self.reference, actual)['summary']['passed'])

    def test_bad_rows_reported(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'bad.csv'
            path.write_text('record_id,category,amount,updated_at\n1,A,10,2026-01-01T00:00:00Z\n1,A,11,2026-01-01T00:00:00Z\n2,A,nope,2026-01-01T00:00:00Z\n3,A,1,now\n', encoding='utf-8')
            records, errors = load_records(path)
            self.assertEqual(len(records), 1)
            self.assertEqual(len(errors), 3)

    def test_timezone_normalization(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'dates.csv'
            path.write_text('record_id,category,amount,updated_at\n1,A,10,2026-01-01T01:00:00+01:00\n', encoding='utf-8')
            records, errors = load_records(path)
            self.assertFalse(errors)
            self.assertEqual(records['1'].updated_at, '2026-01-01T00:00:00Z')

    def test_category_summary(self):
        self.assertEqual(category_totals(self.reference)['A'], {'count': 1, 'total': '10.00'})


if __name__ == '__main__':
    unittest.main()
