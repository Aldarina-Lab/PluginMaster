# Aldarina Lab FFXIV Plugins

Central Dalamud custom repository for the Aldarina Lab plugins: XivMargin, GlamRoute, MeldGuide and House Check-in.

Add this URL in Dalamud under `/xlsettings` → Experimental → **Custom Plugin Repositories**:

`https://aldarina-lab.github.io/PluginMaster/pluginmaster.json`

## How the feed is built

The plugin repositories are private, so their release assets can't be downloaded by Dalamud. The `Publish
PluginMaster` workflow reads each plugin's latest release, copies its ZIP into this site under
`plugins/<InternalName>/<tag>/latest.zip`, and points the download links there. The ZIPs and manifests are public;
the plugin source stays private.

- A plugin with no release yet is left out of the feed.
- A repository the token can't read stops the run, so the published feed is never silently emptied.
- Every manifest must have the matching `InternalName` and Dalamud API level 15.

The workflow runs every hour, on pushes to `main`, by hand, and on a `plugin-released` repository dispatch, so a
new release appears within the hour.

## Tokens

- `PLUGIN_READ_TOKEN` (secret in this repository, required): a fine-grained PAT with resource owner Aldarina-Lab,
  access to the plugin repositories, and **Contents: Read-only**. It is used to read releases and download their ZIPs.
- `PLUGINMASTER_PAT` (secret in a plugin repository, optional): a fine-grained PAT for this repository with
  **Actions: Read and write**, used to send `plugin-released` right after a release. Without it, the hourly run
  picks the release up.

Add a plugin by appending `{"repository": "Aldarina-Lab/<Repo>", "internalName": "<InternalName>"}` to
`plugins.json`.
