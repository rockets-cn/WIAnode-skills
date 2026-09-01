from __future__ import annotations

import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path


SCRIPT_PATH = (
    Path(__file__).parents[1] / "scripts" / "prepare_wianode_td_plugin.py"
)
SPEC = importlib.util.spec_from_file_location("prepare_wianode_td_plugin", SCRIPT_PATH)
assert SPEC and SPEC.loader
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PrepareWianodeTdPluginTests(unittest.TestCase):
    def create_archive(
        self, path: Path, *, unsafe: bool = False, omit_example: bool = False
    ) -> None:
        prefix = "WIAnode-examples-master"
        plugin_dir = f"{prefix}/WIAnode-Touchdesigner-plugin"
        examples_dir = f"{prefix}/WIAnode_Touchdesigner_samples"
        with zipfile.ZipFile(path, "w") as archive:
            archive.writestr(
                f"{plugin_dir}/{MODULE.PLUGIN_NAME}", b"official-plugin"
            )
            archive.writestr(
                f"{plugin_dir}/{MODULE.PLUGIN_SAMPLE_NAME}", b"official-sample"
            )
            for index, relative_path in enumerate(MODULE.REQUIRED_EXAMPLES):
                if omit_example and index == 0:
                    continue
                archive.writestr(f"{examples_dir}/{relative_path}", b"example")
            if unsafe:
                archive.writestr("../outside.txt", b"unsafe")

    def test_extracts_official_plugin_examples_and_reuses_checksum(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            archive_path = root / "official.zip"
            destination = root / "install"
            self.create_archive(archive_path)

            first = MODULE.prepare_bundle(archive_path, destination)
            second = MODULE.prepare_bundle(archive_path, destination)

            self.assertFalse(first["reused"])
            self.assertTrue(second["reused"])
            self.assertEqual(first["repository_url"], MODULE.REPOSITORY_URL)
            self.assertEqual(first["plugin_path"], second["plugin_path"])
            self.assertTrue(Path(first["plugin_path"]).is_file())
            self.assertEqual(len(first["example_paths"]), 15)

    def test_rejects_missing_official_example(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            archive_path = root / "incomplete.zip"
            self.create_archive(archive_path, omit_example=True)

            with self.assertRaisesRegex(ValueError, "Official examples are missing"):
                MODULE.prepare_bundle(archive_path, root / "install")

    def test_rejects_path_traversal(self) -> None:
        with tempfile.TemporaryDirectory() as temp_name:
            root = Path(temp_name)
            archive_path = root / "unsafe.zip"
            self.create_archive(archive_path, unsafe=True)

            with self.assertRaisesRegex(ValueError, "Unsafe archive path"):
                MODULE.prepare_bundle(archive_path, root / "install")

    def test_source_is_dfrobot_repository(self) -> None:
        self.assertEqual(
            MODULE.REPOSITORY_URL,
            "https://github.com/DFRobot/WIAnode-examples",
        )
        self.assertIn("DFRobot/WIAnode-examples", MODULE.DEFAULT_URL)
        self.assertTrue(MODULE.DEFAULT_URL.endswith("/refs/heads/master"))


if __name__ == "__main__":
    unittest.main()
