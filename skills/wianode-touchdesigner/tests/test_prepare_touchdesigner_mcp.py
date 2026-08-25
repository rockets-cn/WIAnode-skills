from __future__ import annotations

import importlib.util
import tempfile
import unittest
from unittest import mock
import zipfile
from pathlib import Path


SCRIPT_PATH = Path(__file__).parents[1] / "scripts" / "prepare_touchdesigner_mcp.py"
SPEC = importlib.util.spec_from_file_location("prepare_touchdesigner_mcp", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrepareTouchDesignerMcpTests(unittest.TestCase):
    def create_archive(self, path: Path, *, unsafe: bool = False) -> None:
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr("mcp_webserver_base.tox", b"tox")
            archive.writestr("import_modules.py", b"setup = True")
            archive.writestr("modules/utils/config.py", b"PORT = 9981")
            if unsafe:
                archive.writestr("../outside.txt", b"unsafe")

    def test_extracts_bundle_and_reuses_matching_release(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            archive_path = root / "bundle.zip"
            destination = root / "install"
            self.create_archive(archive_path)

            first = MODULE.prepare_bundle(archive_path, destination)
            second = MODULE.prepare_bundle(archive_path, destination)

            self.assertFalse(first["reused"])
            self.assertTrue(second["reused"])
            self.assertEqual(first["tox_path"], second["tox_path"])
            self.assertTrue(Path(first["tox_path"]).is_file())
            self.assertTrue((Path(first["bundle_dir"]) / "modules").is_dir())

    def test_download_falls_back_to_curl_without_disabling_tls(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            destination = Path(temp_name) / "bundle.zip"

            def write_download(command: list[str], *, check: bool) -> None:
                self.assertTrue(check)
                self.assertNotIn("--insecure", command)
                Path(command[command.index("--output") + 1]).write_bytes(b"downloaded")

            with (
                mock.patch.object(
                    MODULE.urllib.request,
                    "urlopen",
                    side_effect=MODULE.urllib.error.URLError("certificate failure"),
                ),
                mock.patch.object(MODULE.shutil, "which", return_value="/usr/bin/curl"),
                mock.patch.object(MODULE.subprocess, "run", side_effect=write_download),
            ):
                MODULE.download_archive(MODULE.DEFAULT_URL, destination)

            self.assertEqual(destination.read_bytes(), b"downloaded")

    def test_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            archive_path = root / "unsafe.zip"
            self.create_archive(archive_path, unsafe=True)

            with self.assertRaisesRegex(ValueError, "Unsafe archive path"):
                MODULE.prepare_bundle(archive_path, root / "install")

    def test_rejects_windows_style_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            archive_path = root / "unsafe.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("..\\outside.txt", b"unsafe")

            with self.assertRaisesRegex(ValueError, "Unsafe archive path"):
                MODULE.prepare_bundle(archive_path, root / "install")


if __name__ == "__main__":
    unittest.main()
