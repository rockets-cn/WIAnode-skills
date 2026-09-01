from __future__ import annotations

import hashlib
import json
import unittest
from pathlib import Path


SKILL_DIR = Path(__file__).parents[1]
ASSETS_DIR = SKILL_DIR / "assets"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class BundledTouchDesignerAssetsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.sources = json.loads((ASSETS_DIR / "SOURCES.json").read_text())

    def test_dfrobot_plugin_is_bundled_with_recorded_provenance(self) -> None:
        metadata = self.sources["dfrobot_wianode_plugin"]
        plugin_path = ASSETS_DIR / metadata["bundled_path"]

        self.assertEqual(
            metadata["source_repository"],
            "https://github.com/DFRobot/WIAnode-examples",
        )
        self.assertTrue(plugin_path.is_file())
        self.assertGreater(plugin_path.stat().st_size, 0)
        self.assertEqual(sha256_file(plugin_path), metadata["sha256"])

    def test_touchdesigner_mcp_bundle_keeps_required_layout(self) -> None:
        metadata = self.sources["touchdesigner_mcp_bundle"]
        bundle_dir = ASSETS_DIR / "touchdesigner-mcp-td"
        tox_path = ASSETS_DIR / metadata["bundled_path"]

        self.assertEqual(
            metadata["source_repository"],
            "https://github.com/8beeeaaat/touchdesigner-mcp",
        )
        self.assertTrue(tox_path.is_file())
        self.assertEqual(sha256_file(tox_path), metadata["tox_sha256"])
        self.assertTrue((bundle_dir / "import_modules.py").is_file())
        self.assertTrue((bundle_dir / "modules").is_dir())
        self.assertTrue((bundle_dir / metadata["license_path"].split("/", 1)[1]).is_file())


if __name__ == "__main__":
    unittest.main()
