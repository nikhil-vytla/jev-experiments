# Agent notes

This repository was `jev-experiments/` inside [hatch](https://github.com/nikhil-vytla/hatch) until 2026-10-07. Paths are now relative to this root. Recorded evidence (`*.jsonl`, run outputs, `archive/`, the dated review folders) still names `jev-experiments/...` paths, because they were true when recorded. Leave those as they are.

## Deployment

- The Vercel project `jev-experiments` deploys GitHub `main` of `nikhil-vytla/jev-experiments` to https://jev-experiments.vercel.app.
- Its Root Directory is `experience-prototypes`. The commands are `bun install --frozen-lockfile` and `bun run build`, and the output is `dist`.
- Keep outside-root source access enabled. The build reads much of the repository: `results/`, the study folders (`rewardbench2/`, `judgment-reliability/`, `outcome-framing/`, `visual-search/`, `wardrobe-lab/`, `icon-studio/`, `local-models-and-games/`, `music-arranger-v2/`, `cafe-jev/`), `packages/`, `live-worlds/`, `roadmap/`, and the root `README.md`, `SOURCES.md` and `IDEA_GARDEN.md`. The API functions import `packages/` and `wardrobe-lab/`.
- `vercel.json`'s `ignoreCommand` runs `experience-prototypes/scripts/ignore-build.sh`. It skips a build only when the commit changes nothing outside the paths the build never reads: `archive/`, `.github/`, `adapters/`, `agents/`, `apps/`, `artifacts/`, `extensions/`, `src/`, `tests/`, `tools/`, the dated `*-2026-09-22/` review folders, and a few root files (`AGENTS.md`, `CLAUDE.md`, `NOTES.md`, `_summary.md`, `pyproject.toml`, `uv.lock`, `.oxlintrc.json`, `.oxfmtrc.json`). This list was checked by deleting all of those paths from a clean clone: the build still passed, and `dist/` was byte-identical apart from build timestamps. Any other change builds, including a new top-level folder. Add a path to the list only after the same check.
- The ignore step and the source-view revision links (`scripts/source-revision.ts`) need `.git` in the build, so keep `.git` out of `.vercelignore`. Don't broadly exclude `results` there either.
- Deployment Storage is the Hobby limit to watch (about 95 MB a build). Previews are kept 7 days, production 14.
- After moving files, verify a deployment from a clean checkout (`git clone`, then `cd experience-prototypes && bun install --frozen-lockfile && bun run build`). Locally prepared assets can hide missing inputs.

## CI

The four workflows in `.github/workflows/` run from the repository root. `jev-site.yml` runs on every push and pull request. It builds the site, runs the tests, rebuilds the evidence index and `roadmap/verification/publication-index.json`, then fails on `git diff --exit-code`. The build copies the root `README.md`, `SOURCES.md` and `IDEA_GARDEN.md` into `public/`, so editing any of them (or any other published file) means running the build and `bun run roadmap/verification/publication.ts`, then committing the updated index.
