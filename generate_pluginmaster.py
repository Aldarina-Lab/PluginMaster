#!/usr/bin/env python3
"""Build a Dalamud custom-repository index from immutable GitHub releases.

Plugin repositories are private, so Dalamud can't download their release assets. Each plugin's latest release ZIP is
copied into the published site next to pluginmaster.json, and the download links point there. A plugin with no
release yet is skipped; a repository the token can't see is an error, so a missing token never publishes an empty feed.
"""
from __future__ import annotations
import calendar, json, os, pathlib, re, sys, time, urllib.error, urllib.request, zipfile, io

ROOT = pathlib.Path(__file__).parent
DIST = ROOT / "dist"
OUTPUT = DIST / "pluginmaster.json"
SITE = "https://aldarina-lab.github.io/PluginMaster"
API_LEVEL = 15
SAFE = re.compile(r"[A-Za-z0-9._-]+")
ALLOWED = {"Author", "Name", "Punchline", "Description", "Changelog", "InternalName", "AssemblyVersion", "RepoUrl", "ApplicableVersion", "Tags", "DalamudApiLevel", "IconUrl", "ImageUrls"}

def _open(url: str, accept: str):
    req = urllib.request.Request(url, headers={"Accept": accept, "User-Agent": "Aldarina-Lab-PluginMaster/1"})
    token = os.environ.get("GITHUB_TOKEN")
    if token: req.add_header("Authorization", f"Bearer {token}")
    return urllib.request.urlopen(req, timeout=60)

def get_json(url: str):
    with _open(url, "application/vnd.github+json") as response: return json.load(response)

def get_bytes(url: str) -> bytes:
    with _open(url, "application/octet-stream") as response: return response.read()

def latest_release(repository: str):
    """The latest release, or None when the repository has none yet."""
    try: get_json(f"https://api.github.com/repos/{repository}")
    except urllib.error.HTTPError as e:
        if e.code == 404: raise RuntimeError(f"can't see {repository}: is PLUGIN_READ_TOKEN set and allowed to read it?") from None
        raise
    try: return get_json(f"https://api.github.com/repos/{repository}/releases/latest")
    except urllib.error.HTTPError as e:
        if e.code == 404: return None
        raise

def entry(spec: dict, dist: pathlib.Path = DIST):
    name = spec["internalName"]
    release = latest_release(spec["repository"])
    if release is None:
        print(f"skipping {name}: {spec['repository']} has no release yet", file=sys.stderr); return None
    assets = [a for a in release["assets"] if a["name"].lower().endswith(".zip")]
    if len(assets) != 1: raise RuntimeError(f"{spec['repository']} must publish exactly one plugin ZIP")
    tag = release["tag_name"]
    if not SAFE.fullmatch(tag) or not SAFE.fullmatch(name): raise RuntimeError(f"unsafe tag or name: {tag!r} {name!r}")
    payload = get_bytes(assets[0]["url"])
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        names = {pathlib.PurePosixPath(x).name: x for x in archive.namelist()}
        if f"{name}.json" not in names: raise RuntimeError(f"{name}.json missing from {assets[0]['name']}")
        manifest = json.loads(archive.read(names[f"{name}.json"]))
    if manifest.get("InternalName") != name: raise RuntimeError("InternalName mismatch")
    if int(manifest.get("DalamudApiLevel", 0)) != API_LEVEL: raise RuntimeError(f"Dalamud API level must be {API_LEVEL}")
    target = dist / "plugins" / name / tag / "latest.zip"
    target.parent.mkdir(parents=True, exist_ok=True); target.write_bytes(payload)
    link = f"{SITE}/plugins/{name}/{tag}/latest.zip"
    result = {key: value for key, value in manifest.items() if key in ALLOWED}
    result.update({"DownloadLinkInstall": link, "DownloadLinkTesting": link, "DownloadLinkUpdate": link, "IsHide": False, "IsTestingExclusive": False,
                   "LastUpdate": str(calendar.timegm(time.strptime(release["published_at"], "%Y-%m-%dT%H:%M:%SZ")))})
    return result

def main():
    specs = json.loads((ROOT / "plugins.json").read_text())
    entries = [e for e in (entry(spec) for spec in specs) if e is not None]
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(entries, indent=2) + "\n")
    print(f"published {len(entries)} of {len(specs)} plugins: {', '.join(e['InternalName'] for e in entries) or 'none'}")

if __name__ == "__main__": main()
