# OpenClaw Distribution

OpenClaw can consume the canonical `skills/` directory directly. The
`holo-rss-reader` plugin wrapper also ships `openclaw.plugin.json` under
`plugins/holo-rss-reader/` for plugin-based distribution.

Recommended options:

1. Copy or symlink `skills/holo-rss-reader/` into an OpenClaw workspace `skills/` directory.
2. Publish the individual skill with `clawhub skill publish skills/holo-rss-reader`.
3. Publish the plugin package generated under `dist/plugins/openclaw-holo-rss-reader-plugin.zip` when a plugin wrapper is needed.

This repository does not keep a separate OpenClaw workspace copy. The local
plugin `skills/` directory is generated with `holo-rss-sync-plugin` when
wrapper-level testing is needed.
