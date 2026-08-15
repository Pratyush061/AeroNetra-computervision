#!/usr/bin/env python3
"""
Dataset downloading script.
Prioritizes explicit configurations and prevents automatic large downloads.
"""

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def check_kaggle_cli():
    """Checks if the Kaggle CLI is installed and configured."""
    if not shutil.which("kaggle"):
        print("Error: Kaggle CLI not found.", file=sys.stderr)
        print("Please install it: pip install kaggle", file=sys.stderr)
        return False

    kaggle_json_path = Path.home() / ".kaggle" / "kaggle.json"
    if not kaggle_json_path.exists():
        print("Error: Kaggle credentials not found.", file=sys.stderr)
        print("Please place kaggle.json in ~/.kaggle/ and run:", file=sys.stderr)
        print("  chmod 600 ~/.kaggle/kaggle.json", file=sys.stderr)
        print("For more info: https://github.com/Kaggle/kaggle-api", file=sys.stderr)
        return False
    return True


def download_kaggle_dataset(
    dataset_name: str, dest_dir: Path, dry_run: bool = False, force: bool = False
):
    """Downloads a dataset from Kaggle."""
    if not check_kaggle_cli():
        sys.exit(1)

    if dest_dir.exists() and any(dest_dir.iterdir()):
        if not force:
            print(f"Error: Destination {dest_dir} is not empty.", file=sys.stderr)
            print("Use --force to overwrite.", file=sys.stderr)
            sys.exit(1)
        else:
            print(
                f"Warning: --force used. Existing data in {dest_dir} may be overwritten."
            )

    cmd = [
        "kaggle",
        "datasets",
        "download",
        "-d",
        dataset_name,
        "-p",
        str(dest_dir),
        "--unzip",
    ]

    if dry_run:
        print(f"[DRY-RUN] Would run: {' '.join(cmd)}")
    else:
        print(f"Downloading {dataset_name} to {dest_dir}...")
        try:
            dest_dir.mkdir(parents=True, exist_ok=True)
            subprocess.run(cmd, check=True)
            print("Download and extraction complete.")
        except subprocess.CalledProcessError as e:
            print(f"Error downloading dataset: {e}", file=sys.stderr)
            sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="Download datasets for AeroNetra.")
    parser.add_argument(
        "--dataset",
        required=True,
        help="Name of the dataset (e.g., 'mukuldeshantri/visdrone2019')",
    )
    parser.add_argument("--dest", required=True, help="Destination directory")
    parser.add_argument(
        "--download", action="store_true", help="Explicitly allow downloading"
    )
    parser.add_argument(
        "--force", action="store_true", help="Force overwrite of existing data"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print what would happen without doing it",
    )

    args = parser.parse_args()

    if not args.download and not args.dry_run:
        print(
            "Error: You must explicitly provide the --download flag to download multi-gigabyte datasets.",
            file=sys.stderr,
        )
        print(
            "Example: python scripts/download_dataset.py --dataset ... --dest ... --download",
            file=sys.stderr,
        )
        sys.exit(1)

    dest_path = Path(args.dest)
    download_kaggle_dataset(
        args.dataset, dest_path, dry_run=args.dry_run, force=args.force
    )


if __name__ == "__main__":
    main()
