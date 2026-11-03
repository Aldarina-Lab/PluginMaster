import io, json, pathlib, tempfile, unittest, urllib.error, zipfile
from unittest.mock import patch
import generate_pluginmaster as generator

def plugin_zip(manifest: dict) -> bytes:
    out = io.BytesIO()
    with zipfile.ZipFile(out, "w") as z:
        z.writestr("HouseCheckin.json", json.dumps(manifest)); z.writestr("HouseCheckin.dll", b"dll")
    return out.getvalue()

MANIFEST = {"InternalName": "HouseCheckin", "Name": "House Check-in", "Author": "Aldarina Lab", "DalamudApiLevel": 15, "LoadPriority": 0}
RELEASE = {"tag_name": "v1.0.0", "published_at": "2026-11-02T22:50:00Z", "assets": [{"name": "latest.zip", "url": "https://api/asset/1"}]}
SPEC = {"repository": "Aldarina-Lab/HouseCheckin", "internalName": "HouseCheckin"}

def missing(*args, **kwargs): raise urllib.error.HTTPError("u", 404, "Not Found", None, None)

class Tests(unittest.TestCase):
    def test_configuration_has_unique_internal_names(self):
        specs = json.loads((pathlib.Path(__file__).parent / "plugins.json").read_text())
        self.assertEqual(4, len(specs)); self.assertEqual(4, len({x["internalName"] for x in specs}))
    def test_allowed_manifest_fields_include_required_metadata(self):
        self.assertTrue({"Author", "Name", "Description", "InternalName", "DalamudApiLevel"}.issubset(generator.ALLOWED))
    def test_release_zip_is_copied_into_the_site_and_linked_there(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(generator, "latest_release", return_value=RELEASE), \
             patch.object(generator, "get_bytes", return_value=plugin_zip(MANIFEST)):
            result = generator.entry(SPEC, pathlib.Path(tmp))
            self.assertTrue((pathlib.Path(tmp) / "plugins/HouseCheckin/v1.0.0/latest.zip").is_file())
        link = "https://aldarina-lab.github.io/PluginMaster/plugins/HouseCheckin/v1.0.0/latest.zip"
        self.assertEqual({result["DownloadLinkInstall"], result["DownloadLinkUpdate"], result["DownloadLinkTesting"]}, {link})
        self.assertNotIn("LoadPriority", result); self.assertEqual("1793659800", result["LastUpdate"])
    def test_plugin_without_a_release_is_skipped(self):
        with patch.object(generator, "latest_release", return_value=None): self.assertIsNone(generator.entry(SPEC))
    def test_wrong_api_level_or_name_is_refused(self):
        for manifest in ({**MANIFEST, "DalamudApiLevel": 14}, {**MANIFEST, "InternalName": "Other"}):
            with tempfile.TemporaryDirectory() as tmp, patch.object(generator, "latest_release", return_value=RELEASE), \
                 patch.object(generator, "get_bytes", return_value=plugin_zip(manifest)), self.assertRaises(RuntimeError):
                generator.entry(SPEC, pathlib.Path(tmp))
    def test_unsafe_tag_is_refused(self):
        with patch.object(generator, "latest_release", return_value={**RELEASE, "tag_name": "../x"}), self.assertRaises(RuntimeError):
            generator.entry(SPEC)
    def test_unreadable_repository_is_an_error_but_no_release_is_not(self):
        with patch.object(generator, "get_json", side_effect=missing), self.assertRaises(RuntimeError): generator.latest_release("Aldarina-Lab/X")
        with patch.object(generator, "get_json", side_effect=[{}, urllib.error.HTTPError("u", 404, "Not Found", None, None)]):
            self.assertIsNone(generator.latest_release("Aldarina-Lab/X"))

if __name__ == "__main__": unittest.main()
