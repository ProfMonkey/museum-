"""Run Wonder Atlas checks locally with ZERO GitHub Actions minutes.

Examples:
  python scripts/check_local.py --quick
  python scripts/check_local.py
  python scripts/check_local.py --js-only
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> int:
    print("\n> " + " ".join(cmd), flush=True)
    result = subprocess.run(cmd, cwd=ROOT, check=False)
    return result.returncode


def main() -> int:
    parser = argparse.ArgumentParser(description="Test Wonder Atlas locally. Never uses GitHub Actions.")
    parser.add_argument("--quick", action="store_true", help="Run focused V24 and V32–V41 navigation, taxonomy and interactive modules.")
    parser.add_argument("--js-only", action="store_true", help="Skip Python tests and only check JS syntax.")
    args = parser.parse_args()

    failed = False
    if not args.js_only:
        tests = ["tests/test_wheel_v24.py", "tests/test_mysteries_v32.py", "tests/test_collision_v33.py", "tests/test_civilizations_v34.py", "tests/test_embassies_v35.py", "tests/test_heritage_v36.py", "tests/test_archaeology_v37.py", "tests/test_v40_navigation.py", "tests/test_v39_wheels.py", "tests/test_object_hub_v41.py"] if args.quick else ["tests"]
        failed |= run([sys.executable, "-m", "pytest", "-q", *tests]) != 0
    node = shutil.which("node")
    if node:
        files = sorted((ROOT / "static").glob("*.js"))
        print(f"\nChecking {len(files)} first-party JavaScript files locally.", flush=True)
        for file in files:
            failed |= run([node, "--check", str(file.relative_to(ROOT))]) != 0
    else:
        print("\nNode.js not installed; JavaScript syntax check skipped.", flush=True)
    print("\nLocal verification " + ("FAILED" if failed else "FINISHED") +
          " — no remote runners launched.", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
