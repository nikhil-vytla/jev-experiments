"""Check runtime plus routing against archived Git source, without providers or GPUs."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tarfile
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROADMAP = HERE.parent
ROOT = ROADMAP.parent
APP_FILES = {"ModelRoutingLab.tsx", "evidence-links.ts", "web-handler.ts"}
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument("--base", default="HEAD", help="Git base to archive before overlaying authored runtime/router files")
parser.add_argument("--output", type=Path, default=HERE / "isolated-check.json")
args = parser.parse_args()
base = subprocess.check_output(["git", "rev-parse", args.base], cwd=ROOT, text=True).strip()
rows = []
manifest = {}
# No credential loading, client CLI sessions, model installation or inference is needed.
env = {key: value for key, value in os.environ.items()
       if not any(marker in key.upper() for marker in ("API_KEY", "TOKEN", "SECRET", "PASSWORD"))
       and not key.startswith(("JEV_", "OPENCODE_", "ANTHROPIC_", "OPENAI_", "AWS_"))}


def copy_source(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    data = source.read_bytes()
    destination.write_bytes(data)
    manifest[str(source.relative_to(ROOT))] = hashlib.sha256(data).hexdigest()


with tempfile.TemporaryDirectory(prefix="jev-routing-isolated-") as temporary:
    destination = Path(temporary)
    with tempfile.TemporaryFile() as archive:
        subprocess.run(["git", "archive", base], cwd=ROOT, stdout=archive, check=True)
        archive.seek(0)
        with tarfile.open(fileobj=archive) as source:
            source.extractall(destination, filter="data")
    for folder in (ROADMAP / "runtime", HERE):
        for source in folder.rglob("*"):
            if (not source.is_file() or "__pycache__" in source.parts
                    or source.name in APP_FILES
                    or source.name in {"standalone-check.json", "isolated-check.json"}
                    or ".local." in source.name):
                continue
            copy_source(source, destination / source.relative_to(ROOT))
    for source in (ROADMAP / "package.json", ROADMAP / "bun.lock", ROADMAP / "mac/models.json"):
        copy_source(source, destination / source.relative_to(ROOT))
    lab = destination / "roadmap"
    (lab / "tsconfig.json").write_text(json.dumps({
        "compilerOptions": {"target": "ES2022", "module": "ESNext", "moduleResolution": "bundler",
                            "lib": ["ES2022", "DOM", "DOM.Iterable"], "strict": True, "skipLibCheck": True,
                            "noEmit": True, "allowImportingTsExtensions": True, "types": ["bun"]},
        "include": ["runtime/**/*.ts", "routing/**/*.ts"],
    }, indent=2) + "\n")
    # The retained patch still names hatch-era a/jev-experiments/ paths; -p2 strips that prefix.
    commands = [
        (["git", "apply", "-p2", "--check", "roadmap/runtime/existing-contracts.patch"], "."),
        (["git", "apply", "-p2", "roadmap/runtime/existing-contracts.patch"], "."),
        (["bun", "install", "--frozen-lockfile"], "adapters/typescript"),
        (["bun", "install", "--frozen-lockfile"], "roadmap"),
        (["bun", "test", "roadmap/runtime", "roadmap/routing"], "."),
        (["bun", "x", "--no-install", "tsc", "--noEmit", "-p", "tsconfig.json"], "roadmap"),
        (["python3", "roadmap/routing/fresh_install.py"], "."),
    ]
    for command, cwd in commands:
        start = time.perf_counter()
        result = subprocess.run(command, cwd=destination / cwd, env=env, capture_output=True, text=True, timeout=120)
        rows.append({"command": command, "cwd": cwd, "exitCode": result.returncode,
                     "elapsedSeconds": time.perf_counter() - start,
                     "output": (result.stdout + result.stderr).replace(str(destination), "<isolated-root>")[-16000:]})
        print(("PASS " if result.returncode == 0 else "FAIL ") + " ".join(command), flush=True)
        if result.returncode:
            break
    fresh = lab / "routing/fresh-install.json"
    fresh_record = json.loads(fresh.read_text()) if len(rows) == len(commands) and fresh.exists() else None
report = {
    "baseCommit": base,
    "scope": "Runtime plus routing SDK/CLI/MCP, excluding later app component, evidence-link module and web handler.",
    "extraDependency": "Only roadmap/mac/models.json; no Mac runtime implementation, training code or weights copied.",
    "providerCalls": False,
    "gpuCalls": False,
    "copiedSourceSha256": manifest,
    "checks": rows,
    "freshInstall": ({key: fresh_record[key] for key in ("bundleBytes", "bundleSha256", "mailUnchanged", "uninstalled")}
                     if fresh_record else None),
    "passed": len(rows) == len(commands) and all(row["exitCode"] == 0 for row in rows),
}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(report, indent=2) + "\n")
if not report["passed"]:
    raise SystemExit(1)
