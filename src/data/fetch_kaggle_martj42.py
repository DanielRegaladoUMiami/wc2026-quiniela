"""Fetch the martj42/international-football-results dataset from Kaggle.

Provides every international men's football match since 1872 with goals, venue, neutral
flag and tournament — the backbone of the unified match log. Auto-updated by the dataset
owner; we re-pull on every `make data-refresh`.

Requires `KAGGLE_USERNAME` and `KAGGLE_KEY` env vars (or `~/.kaggle/kaggle.json`).
"""

from __future__ import annotations

import os
import sys
import zipfile
from pathlib import Path

DATASET = "martj42/international-football-results-from-1872-to-2017"
OUT_DIR = Path("data/raw/matches/kaggle_martj42")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    if not (os.environ.get("KAGGLE_KEY") or Path.home().joinpath(".kaggle/kaggle.json").exists()):
        print(
            "ERROR: Kaggle credentials missing. Set KAGGLE_USERNAME + KAGGLE_KEY or place kaggle.json.",
            file=sys.stderr,
        )
        return 1

    # Use the Kaggle Python API rather than the `kaggle` CLI: portable across
    # environments (no PATH / console-script dependency) and works the same in CI.
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
    except ImportError:
        print("ERROR: kaggle package not installed. Run `uv sync`.", file=sys.stderr)
        return 1

    api = KaggleApi()
    api.authenticate()

    print(f"Downloading {DATASET} → {OUT_DIR}")
    api.dataset_download_files(DATASET, path=str(OUT_DIR), unzip=True, quiet=False)

    # dataset_download_files(unzip=True) usually removes the zip, but clean up any leftover.
    for zip_path in OUT_DIR.glob("*.zip"):
        print(f"Unzipping leftover {zip_path.name}")
        with zipfile.ZipFile(zip_path) as zf:
            zf.extractall(OUT_DIR)
        zip_path.unlink()

    print("Done. Files:")
    for p in sorted(OUT_DIR.iterdir()):
        print(f"  {p.name}  ({p.stat().st_size:,} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
