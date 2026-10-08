#!/bin/sh
# Vercel's ignoreCommand (vercel.json). Exit 0 skips the build; anything else builds.
#
# The build reads most of the repository: results/, the study folders, packages/, live-worlds/,
# roadmap/, the root README.md, SOURCES.md and IDEA_GARDEN.md, and .git for source revisions.
# It reads none of the paths excluded below. Deleting all of them from a clean clone leaves dist/
# byte-identical apart from build timestamps, so a commit that changes only these paths is skipped.
# Keep this list to paths that are never built: a missing entry costs one extra build, a wrong
# entry ships a stale site. A failed diff (no parent commit in a shallow clone) builds.
cd "$(git rev-parse --show-toplevel)" || exit 1
if git diff --quiet HEAD^ HEAD -- . \
  ':(exclude)archive' ':(exclude).github' ':(exclude)adapters' ':(exclude)agents' ':(exclude)apps' ':(exclude)artifacts' ':(exclude)extensions' \
  ':(exclude)gateway-accounting-2026-09-22' ':(exclude)release-implementation-2026-09-22' \
  ':(exclude)scene-lifetimes-2026-09-22' ':(exclude)typed-runtime-2026-09-22' ':(exclude)src' ':(exclude)tests' ':(exclude)tools' \
  ':(exclude)AGENTS.md' ':(exclude)CLAUDE.md' ':(exclude)NOTES.md' ':(exclude)_summary.md' ':(exclude)pyproject.toml' ':(exclude)uv.lock' \
  ':(exclude).oxlintrc.json' ':(exclude).oxfmtrc.json'; then
  exit 0
fi
exit 1
