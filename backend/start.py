"""Production entrypoint for Docker / Railway."""
from __future__ import annotations

import os
import subprocess
import sys


def run(cmd: list[str]) -> None:
    print(f"[WorkTaskMe] {' '.join(cmd)}", flush=True)
    subprocess.check_call(cmd)


def main() -> None:
    os.chdir("/app" if os.path.isdir("/app") else os.getcwd())
    run([sys.executable, "manage.py", "migrate", "--noinput"])
    run([sys.executable, "manage.py", "collectstatic", "--noinput"])
    if os.getenv("SEED_DEMO", "").lower() in ("1", "true", "yes"):
        try:
            run([sys.executable, "manage.py", "seed_demo"])
        except subprocess.CalledProcessError as exc:
            print(f"[WorkTaskMe] seed_demo skipped: {exc}", flush=True)

    port = os.getenv("PORT", "8000")
    os.execvp(
        "daphne",
        ["daphne", "-b", "0.0.0.0", "-p", port, "config.asgi:application"],
    )


if __name__ == "__main__":
    main()
