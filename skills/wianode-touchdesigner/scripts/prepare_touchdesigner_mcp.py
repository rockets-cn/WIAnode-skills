#!/usr/bin/env python3
"""Download and safely unpack the official TouchDesigner MCP component bundle."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import stat
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path, PurePosixPath


DEFAULT_URL = (
    "https://github.com/8beeeaaat/touchdesigner-mcp/releases/latest/download/"
    "touchdesigner-mcp-td.zip"
)
DEFAULT_DESTINATION = Path.home() / ".codex" / "tools" / "touchdesigner-mcp"
MAX_MEMBERS = 5_000
MAX_UNCOMPRESSED_BYTES = 50 * 1024 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare the official touchdesigner-mcp .tox bundle for import."
    )
    parser.add_argument(
        "--archive",
        type=Path,
        help="Use an existing touchdesigner-mcp-td.zip instead of downloading it.",
    )
    parser.add_argument(
        "--destination",
        type=Path,
        default=DEFAULT_DESTINATION,
        help=f"Extraction root (default: {DEFAULT_DESTINATION}).",
    )
    return parser.parse_args()


def download_archive(url: str, destination: Path) -> None:
    request = urllib.request.Request(url, headers={"User-Agent": "WIAnode-skills/1"})
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            with destination.open("wb") as output:
                shutil.copyfileobj(response, output)
    except urllib.error.URLError:
        curl_path = shutil.which("curl")
        if not curl_path:
            raise
        subprocess.run(
            [
                curl_path,
                "--fail",
                "--location",
                "--silent",
                "--show-error",
                "--output",
                str(destination),
                url,
            ],
            check=True,
        )


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def validate_archive(archive: zipfile.ZipFile) -> None:
    members = archive.infolist()
    if len(members) > MAX_MEMBERS:
        raise ValueError(f"Archive has too many entries: {len(members)}")

    total_size = sum(member.file_size for member in members)
    if total_size > MAX_UNCOMPRESSED_BYTES:
        raise ValueError(f"Archive expands beyond {MAX_UNCOMPRESSED_BYTES} bytes")

    for member in members:
        path = PurePosixPath(member.filename)
        if path.is_absolute() or ".." in path.parts or "\\" in member.filename:
            raise ValueError(f"Unsafe archive path: {member.filename}")
        file_mode = member.external_attr >> 16
        if stat.S_ISLNK(file_mode):
            raise ValueError(f"Archive contains a symbolic link: {member.filename}")


def locate_bundle(root: Path) -> Path:
    tox_files = list(root.rglob("mcp_webserver_base.tox"))
    if len(tox_files) != 1:
        raise ValueError(f"Expected one mcp_webserver_base.tox, found {len(tox_files)}")

    bundle_dir = tox_files[0].parent
    if not (bundle_dir / "import_modules.py").is_file():
        raise ValueError("Bundle is missing import_modules.py")
    if not (bundle_dir / "modules").is_dir():
        raise ValueError("Bundle is missing the modules directory")
    return tox_files[0]


def prepare_bundle(archive_path: Path, destination: Path) -> dict[str, object]:
    checksum = sha256_file(archive_path)
    destination = destination.expanduser().resolve()
    release_dir = destination / checksum[:12]

    if release_dir.exists():
        tox_path = locate_bundle(release_dir)
        return {
            "reused": True,
            "sha256": checksum,
            "bundle_dir": str(tox_path.parent),
            "tox_path": str(tox_path),
        }

    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".prepare-", dir=destination) as temp_name:
        staging_dir = Path(temp_name) / "payload"
        staging_dir.mkdir()
        with zipfile.ZipFile(archive_path) as archive:
            validate_archive(archive)
            archive.extractall(staging_dir)
        tox_path = locate_bundle(staging_dir)
        relative_tox_path = tox_path.relative_to(staging_dir)
        staging_dir.replace(release_dir)

    final_tox_path = release_dir / relative_tox_path
    return {
        "reused": False,
        "sha256": checksum,
        "bundle_dir": str(final_tox_path.parent),
        "tox_path": str(final_tox_path),
    }


def main() -> int:
    args = parse_args()
    try:
        if args.archive:
            archive_path = args.archive.expanduser().resolve()
            if not archive_path.is_file():
                raise FileNotFoundError(f"Archive not found: {archive_path}")
            result = prepare_bundle(archive_path, args.destination)
        else:
            with tempfile.TemporaryDirectory(prefix="touchdesigner-mcp-") as temp_name:
                archive_path = Path(temp_name) / "touchdesigner-mcp-td.zip"
                download_archive(DEFAULT_URL, archive_path)
                result = prepare_bundle(archive_path, args.destination)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (
        OSError,
        ValueError,
        subprocess.CalledProcessError,
        zipfile.BadZipFile,
    ) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
