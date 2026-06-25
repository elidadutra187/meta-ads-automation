# -*- coding: utf-8 -*-
"""
Keep a gcloud auth login process alive while the browser returns an auth code.

Usage:
1. Run this script.
2. It writes GCLOUD_LOGIN_LINK.txt and opens the browser.
3. Put the returned code in GCLOUD_LOGIN_CODE.txt.
4. The script sends the code to the same gcloud process.
"""
from __future__ import annotations

import re
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
GCLOUD = Path.home() / "google-cloud-sdk-install" / "google-cloud-sdk" / "bin" / "gcloud.cmd"
LINK_PATH = BASE_DIR / "GCLOUD_LOGIN_LINK.txt"
CODE_PATH = BASE_DIR / "GCLOUD_LOGIN_CODE.txt"
LOG_PATH = BASE_DIR / "GCLOUD_LOGIN_HELPER.log"


def log(message: str) -> None:
    with LOG_PATH.open("a", encoding="utf-8") as fh:
        fh.write(message + "\n")
    print(message, flush=True)


def main() -> int:
    LINK_PATH.unlink(missing_ok=True)
    CODE_PATH.unlink(missing_ok=True)
    LOG_PATH.unlink(missing_ok=True)

    proc = subprocess.Popen(
        [str(GCLOUD), "auth", "login", "--no-launch-browser"],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        encoding="utf-8",
        errors="replace",
        bufsize=1,
    )

    auth_url = ""
    assert proc.stdout is not None
    while True:
        line = proc.stdout.readline()
        if not line:
            break
        log(line.rstrip())
        match = re.search(r"https://accounts\.google\.com/\S+", line)
        if match:
            auth_url = match.group(0)
            LINK_PATH.write_text(auth_url, encoding="utf-8")
            webbrowser.open(auth_url)
            log(f"LINK_SAVED={LINK_PATH}")
            break

    if not auth_url:
        log("Nao foi possivel capturar o link de autenticacao.")
        return proc.wait(timeout=30)

    log(f"Aguardando codigo em {CODE_PATH}")
    for _ in range(900):
        if CODE_PATH.exists():
            code = CODE_PATH.read_text(encoding="utf-8").strip()
            if code:
                assert proc.stdin is not None
                proc.stdin.write(code + "\n")
                proc.stdin.flush()
                log("Codigo enviado ao gcloud.")
                break
        time.sleep(1)
    else:
        proc.kill()
        log("Tempo esgotado aguardando codigo.")
        return 1

    assert proc.stdout is not None
    for line in proc.stdout:
        log(line.rstrip())

    return proc.wait()


if __name__ == "__main__":
    sys.exit(main())

