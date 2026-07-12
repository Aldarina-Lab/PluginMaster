import json, pathlib, unittest
from unittest.mock import patch
import generate_pluginmaster as generator

class Tests(unittest.TestCase):
    def test_configuration_has_unique_internal_names(self):
        specs = json.loads((pathlib.Path(__file__).parent / "plugins.json").read_text())
        self.assertEqual(3, len(specs)); self.assertEqual(3, len({x["internalName"] for x in specs}))
    def test_allowed_manifest_fields_include_required_metadata(self):
        self.assertTrue({"Author", "Name", "Description", "InternalName", "DalamudApiLevel"}.issubset(generator.ALLOWED))

if __name__ == "__main__": unittest.main()
