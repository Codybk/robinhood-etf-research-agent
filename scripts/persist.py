from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BRANCH = os.environ.get("GITHUB_REF_NAME", "main")
BASE = os.environ["SCAN_BASE_SHA"]


def git(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], cwd=ROOT, text=True, capture_output=True, check=check)


def main() -> None:
    with tempfile.TemporaryDirectory() as tmp_name:
        tmp = Path(tmp_name)
        shutil.copytree(ROOT / "state", tmp / "state")
        for attempt in range(4):
            git("fetch", "origin", BRANCH)
            remote = git("rev-parse", f"origin/{BRANCH}").stdout.strip()
            changed = git("diff", "--name-only", f"{BASE}..{remote}").stdout.splitlines() if remote != BASE else []
            if any(path == "state" or path.startswith("state/") for path in changed):
                raise SystemExit("REFUSING TO PERSIST: remote paper state advanced after this scan began")
            git("reset", "--hard", remote)
            target = ROOT / "state"
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(tmp / "state", target)
            subprocess.run(["python3", "-m", "src.dashboard"], cwd=ROOT, check=True)
            git("add", "state", "docs/index.html")
            if git("diff", "--cached", "--quiet", check=False).returncode == 0:
                print("No generated state change")
                return
            git("config", "user.name", "etf-research-agent")
            git("config", "user.email", "actions@users.noreply.github.com")
            git("commit", "-m", "paper scan")
            pushed = git("push", "origin", f"HEAD:{BRANCH}", check=False)
            if pushed.returncode == 0:
                print("Paper state persisted")
                return
            # A source-only race is safe to retry; a state race is rejected above.
        raise SystemExit("Failed to persist paper state after four conflict-safe attempts")


if __name__ == "__main__":
    main()
