#!/usr/bin/env python3
"""Build a Dalamud custom-repository index from immutable GitHub releases."""
from __future__ import annotations
import json, os, pathlib, shutil, tempfile, time, urllib.request, zipfile

ROOT = pathlib.Path(__file__).parent
OUTPUT = ROOT / "dist" / "pluginmaster.json"
ALLOWED = {"Author", "Name", "Punchline", "Description", "Changelog", "InternalName", "AssemblyVersion", "RepoUrl", "ApplicableVersion", "Tags", "DalamudApiLevel", "IconUrl", "ImageUrls"}

def get_json(url: str):
    req = urllib.request.Request(url, headers={"Accept":"application/vnd.github+json", "User-Agent":"Aldarina-Lab-PluginMaster/1"})
    token = os.environ.get("GITHUB_TOKEN")
    if token: req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as response: return json.load(response)

def get_bytes(url: str) -> bytes:
    req = urllib.request.Request(url, headers={"Accept":"application/octet-stream", "User-Agent":"Aldarina-Lab-PluginMaster/1"})
    token = os.environ.get("GITHUB_TOKEN")
    if token: req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=60) as response: return response.read()

def entry(spec: dict) -> dict:
    release = get_json(f"https://api.github.com/repos/{spec['repository']}/releases/latest")
    assets = [a for a in release["assets"] if a["name"].lower().endswith(".zip")]
    if len(assets) != 1: raise RuntimeError(f"{spec['repository']} must publish exactly one plugin ZIP")
    asset = assets[0]; payload = get_bytes(asset["url"])
    with tempfile.TemporaryDirectory() as tmp:
        path = pathlib.Path(tmp) / asset["name"]; path.write_bytes(payload)
        with zipfile.ZipFile(path) as archive:
            manifest_name = f"{spec['internalName']}.json"
            names = {pathlib.PurePosixPath(x).name: x for x in archive.namelist()}
            if manifest_name not in names: raise RuntimeError(f"{manifest_name} missing from {asset['name']}")
            manifest = json.loads(archive.read(names[manifest_name]))
    if manifest.get("InternalName") != spec["internalName"]: raise RuntimeError("InternalName mismatch")
    if int(manifest.get("DalamudApiLevel", 0)) != 15: raise RuntimeError("Dalamud API level must be 15")
    result = {key: value for key, value in manifest.items() if key in ALLOWED}
    result.update({"DownloadLinkInstall":asset["browser_download_url"], "DownloadLinkTesting":asset["browser_download_url"], "DownloadLinkUpdate":asset["browser_download_url"], "IsHide":False, "IsTestingExclusive":False, "LastUpdate":str(int(time.mktime(time.strptime(release["published_at"], "%Y-%m-%dT%H:%M:%SZ"))))})
    return result

def main():
    specs = json.loads((ROOT / "plugins.json").read_text())
    prior = OUTPUT.read_text() if OUTPUT.exists() else None
    entries = [entry(spec) for spec in specs]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if prior: (OUTPUT.parent / "pluginmaster.previous.json").write_text(prior)
    OUTPUT.write_text(json.dumps(entries, indent=2) + "\n")

if __name__ == "__main__": main()
