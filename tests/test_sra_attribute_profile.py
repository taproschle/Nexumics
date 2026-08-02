import csv
from pathlib import Path
import tempfile
import unittest

from nexumics.sra_attribute_profile import profile_sra_attributes, write_attribute_profile


class SraAttributeProfileTests(unittest.TestCase):
    def test_profile_sra_attributes_counts_and_examples(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            batch_dir = root / "batches" / "job"
            batch_dir.mkdir(parents=True)
            input_path = batch_dir / "sra-sample-attributes-batch-000001.csv"
            fieldnames = [
                "sample_accession",
                "biosample_accession",
                "attribute_name",
                "attribute_value",
                "normalized_attribute_name",
                "attribute_category",
            ]
            with input_path.open("w", encoding="utf-8", newline="") as handle:
                writer = csv.DictWriter(handle, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow({"attribute_name": "geo loc name", "attribute_value": "Chile"})
                writer.writerow({"attribute_name": "geo_loc_name", "attribute_value": "USA"})
                writer.writerow({"attribute_name": "host", "attribute_value": "Homo sapiens"})

            rows = profile_sra_attributes(input_dir=root)

            self.assertEqual(rows[0].normalized_attribute_name, "geo_loc_name")
            self.assertEqual(rows[0].count, 2)
            self.assertEqual(rows[0].attribute_category, "spatiotemporal")
            self.assertEqual(rows[0].distinct_value_count, 2)
            self.assertIn("Chile", rows[0].example_values)
            self.assertEqual(rows[1].normalized_attribute_name, "host")

    def test_write_attribute_profile(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            output_path = Path(tmp) / "profile.csv"
            rows = profile_sra_attributes(input_dir=_write_profile_fixture(Path(tmp)))

            write_attribute_profile(rows, output_path)

            with output_path.open(encoding="utf-8", newline="") as handle:
                written = list(csv.DictReader(handle))

            self.assertEqual(written[0]["normalized_attribute_name"], "host")
            self.assertEqual(written[0]["attribute_category"], "host")


def _write_profile_fixture(root: Path) -> Path:
    input_path = root / "sra-sample-attributes-batch-000001.csv"
    fieldnames = ["attribute_name", "attribute_value"]
    with input_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow({"attribute_name": "host", "attribute_value": "human"})
    return root
