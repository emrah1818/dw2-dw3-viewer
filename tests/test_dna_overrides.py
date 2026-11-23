"""Regression tests for portable DNA override rules."""
import unittest

from dw2studio.core.dna_overrides import DnaOverrides


class DnaOverridesTests(unittest.TestCase):
    def test_roundtrip_and_unordered_partners(self):
        mod = DnaOverrides(valid_ids={10, 20, 30})
        mod.add(20, 10, 30, 3)
        self.assertEqual(mod.resolve(10, 20), (30, 3))
        self.assertIsNone(mod.resolve(10, 30))
        restored = DnaOverrides.from_json(mod.to_json(), valid_ids={10, 20, 30})
        self.assertEqual(restored.resolve(10, 20), (30, 3))

    def test_duplicate_rejected(self):
        mod = DnaOverrides()
        mod.add(1, 2, 3, 2)
        with self.assertRaises(ValueError):
            mod.add(2, 1, 4, 3)

    def test_replace_and_delete(self):
        mod = DnaOverrides()
        mod.add(1, 2, 3, 1)
        mod.set(2, 1, 4, 3)
        self.assertEqual(mod.resolve(1, 2), (4, 3))
        self.assertTrue(mod.remove(2, 1))
        self.assertIsNone(mod.resolve(1, 2))

    def test_invalid_replacement_is_atomic(self):
        mod = DnaOverrides()
        mod.add(1, 2, 3, 1)
        with self.assertRaises(ValueError):
            mod.set(1, 2, 999, 2)
        self.assertEqual(mod.resolve(1, 2), (3, 1))

    def test_invalid_inputs(self):
        for args in ((1, 1, 3, 2), (1, 2, 256, 2), (1, 2, 3, 4),
                     (True, 2, 3, 2), (1, 2, 3, True)):
            with self.subTest(args=args), self.assertRaises(ValueError):
                DnaOverrides().add(*args)
        with self.assertRaises(ValueError):
            DnaOverrides(valid_ids={1, 2}).add(1, 2, 3, 3)

    def test_bad_manifest(self):
        for data in ({}, {'format': 'dw2-dna-overrides', 'version': 2, 'rules': []},
                     {'format': 'dw2-dna-overrides', 'version': 1, 'rules': [{'a': 1}]}):
            with self.subTest(data=data), self.assertRaises(ValueError):
                DnaOverrides.from_dict(data)


if __name__ == '__main__':
    unittest.main()
