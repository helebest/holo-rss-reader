# Hermes Distribution

Hermes can consume the canonical `skills/` directory directly. The root
`skills/` directory remains the source of truth so Hermes external skill
directories, direct GitHub/path installs, and well-known discovery continue to
work without depending on the Codex/Claude plugin wrapper.

Recommended options:

1. Add this repository's `skills/` directory to Hermes as an external skill directory.
2. Install from a GitHub path after the repository is published.
3. Host `dist/site/.well-known/skills/index.json` and install through Hermes well-known discovery.

This repository does not keep a separate Hermes skill copy. Build outputs are
generated from `skills/`.
