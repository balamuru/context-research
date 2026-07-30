# context-research

## Layout

- **`scroll-stoppers/`** — the Claude Code plugin itself (portable —
  see [`scroll-stoppers/README.md`](./scroll-stoppers/README.md) for how it
  works and how to install/run it elsewhere).
- **`output/`** — example outputs from running the plugin (ranked data,
  mined brief, rendered dashboard). **Not tracked in git** — these are
  fully regenerable by running the plugin against a niche (see the
  scroll-stoppers README's "Running the engine directly" section), so
  keeping them out of version control avoids bloating history with
  data that goes stale and can be reproduced on demand. They're kept on
  disk as a working example/reference of what a real run produces.

## Getting started

See [`scroll-stoppers/README.md`](./scroll-stoppers/README.md).
