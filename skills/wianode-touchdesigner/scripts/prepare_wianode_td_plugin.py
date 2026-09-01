#!/usr/bin/env python3
"""Download and safely unpack DFRobot's official WIAnode TouchDesigner files."""

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


REPOSITORY_URL = "https://github.com/DFRobot/WIAnode-examples"
DEFAULT_URL = (
    "https://codeload.github.com/DFRobot/WIAnode-examples/zip/refs/heads/master"
)
DEFAULT_DESTINATION = (
    Path.home()
    / ".codex"
    / "tools"
    / "wianode-touchdesigner"
    / "DFRobot-WIAnode-examples"
)
PLUGIN_NAME = "WIAnode_plugin_10828.tox"
PLUGIN_SAMPLE_NAME = "WIAnode_plugin_10828_sample.toe"
REQUIRED_EXAMPLES = (
    "01.WIAnode-TD-button/wianode-button.toe",
    "02.WIAnode-TD-knob/wianode-knob.toe",
    "03.WIAnode-TD-microphone/wianode-microphone.toe",
    "04.WIAnode-TD-light/wianode-light.toe",
    "05.WIAnode-TD-ultrasonic/wianode-distance.toe",
    "06.WIAnode-TD-mmwave/wianode-mmwave.toe",
    "07.WIAnode-TD-accelerometer/wianode-accelerometer.toe",
    "08.WIAnode-TD-gesture/wianode-gesture.toe",
    "09.WIAnode-TD-LED/wianode-led.toe",
    "10.WIAnode-TD-servo300/wianode-servo300.toe",
    "11.WIAnode-TD-IO-TD-touch/WIAnode-IO-touch.toe",
    "12.WIAnode-TD-IO-TD-hall/WIAnode-hall.toe",
    "13.WIAnode-TD-IO-TD-tem&humi/WIAnode-tem&humi.toe",
    "14.WiaNode-TD-I2C-TD-color/WiaNode-I2C-color.toe",
    "15.WiaNode-TD-IO-TD-envionment/WiaNode-envionment.toe",
)
MAX_MEMBERS = 5_000
MAX_UNCOMPRESSED_BYTES = 500 * 1024 * 1024


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare DFRobot's official WIAnode TouchDesigner plugin and examples."
    )
    parser.add_argument(
        "--archive",
        type=Path,
        help="Use an existing DFRobot/WIAnode-examples ZIP archive.",
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
    if sum(member.file_size for member in members) > MAX_UNCOMPRESSED_BYTES:
        raise ValueError(f"Archive expands beyond {MAX_UNCOMPRESSED_BYTES} bytes")

    for member in members:
        path = PurePosixPath(member.filename)
        if path.is_absolute() or ".." in path.parts or "\\" in member.filename:
            raise ValueError(f"Unsafe archive path: {member.filename}")
        if stat.S_ISLNK(member.external_attr >> 16):
            raise ValueError(f"Archive contains a symbolic link: {member.filename}")


def locate_official_files(root: Path) -> dict[str, object]:
    plugins = [
        path
        for path in root.rglob(PLUGIN_NAME)
        if path.parent.name == "WIAnode-Touchdesigner-plugin"
    ]
    if len(plugins) != 1:
        raise ValueError(f"Expected one official {PLUGIN_NAME}, found {len(plugins)}")

    plugin_path = plugins[0]
    plugin_sample_path = plugin_path.with_name(PLUGIN_SAMPLE_NAME)
    if not plugin_sample_path.is_file():
        raise ValueError(f"Official plugin sample is missing: {PLUGIN_SAMPLE_NAME}")
    if plugin_path.stat().st_size == 0 or plugin_sample_path.stat().st_size == 0:
        raise ValueError("Official plugin or plugin sample is empty")

    repository_root = plugin_path.parent.parent
    examples_dir = repository_root / "WIAnode_Touchdesigner_samples"
    missing = [name for name in REQUIRED_EXAMPLES if not (examples_dir / name).is_file()]
    if missing:
        raise ValueError(f"Official examples are missing: {', '.join(missing)}")

    return {
        "repository_root": repository_root,
        "plugin_path": plugin_path,
        "plugin_sample_path": plugin_sample_path,
        "examples_dir": examples_dir,
        "example_paths": [examples_dir / name for name in REQUIRED_EXAMPLES],
    }


def prepare_bundle(archive_path: Path, destination: Path) -> dict[str, object]:
    checksum = sha256_file(archive_path)
    destination = destination.expanduser().resolve()
    release_dir = destination / checksum[:12]

    if release_dir.exists():
        located = locate_official_files(release_dir)
        reused = True
    else:
        destination.mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix=".prepare-", dir=destination) as temp_name:
            staging_dir = Path(temp_name) / "payload"
            staging_dir.mkdir()
            with zipfile.ZipFile(archive_path) as archive:
                validate_archive(archive)
                archive.extractall(staging_dir)
            locate_official_files(staging_dir)
            staging_dir.replace(release_dir)
        located = locate_official_files(release_dir)
        reused = False

    return {
        "reused": reused,
        "repository_url": REPOSITORY_URL,
        "source_archive_url": DEFAULT_URL,
        "sha256": checksum,
        "repository_root": str(located["repository_root"]),
        "plugin_path": str(located["plugin_path"]),
        "plugin_sample_path": str(located["plugin_sample_path"]),
        "examples_dir": str(located["examples_dir"]),
        "example_paths": [str(path) for path in located["example_paths"]],
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
            with tempfile.TemporaryDirectory(prefix="wianode-td-plugin-") as temp_name:
                archive_path = Path(temp_name) / "DFRobot-WIAnode-examples.zip"
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
