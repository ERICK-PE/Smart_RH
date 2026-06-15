"""Provide a project-local temp fallback when the OS temp directory is broken."""

from __future__ import annotations

import os
from pathlib import Path
import tempfile


def _configure_project_tmp() -> None:
    project_tmp = Path(__file__).resolve().parent / ".tmp"
    project_tmp.mkdir(exist_ok=True)
    temp_path = str(project_tmp)

    for env_name in ("TMPDIR", "TEMP", "TMP"):
        os.environ[env_name] = temp_path

    tempfile.tempdir = temp_path


try:
    tempfile.gettempdir()
except FileNotFoundError:
    _configure_project_tmp()
