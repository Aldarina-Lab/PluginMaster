# Aldarina Lab FFXIV Plugins

Central Dalamud custom repository for XivMargin, GlamRoute, and MeldGuide.

After the first successful Pages deployment, add this URL in Dalamud's **Custom Plugin Repositories** settings:

`https://aldarina-lab.github.io/FFXIVPlugins/pluginmaster.json`

The feed is public and unauthenticated. Each entry points to an immutable release ZIP in its independent plugin repository.

## Release authentication

Create a fine-grained PAT scoped to `Aldarina-Lab/FFXIVPlugins` with Actions write access. Store it in each plugin repository as `PLUGINMASTER_PAT`. Rotate it according to the organization policy. The token is only used to send the `plugin-released` repository dispatch event.
